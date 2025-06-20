import asyncio
import configparser
import logging
import os
import socket

# --- Configuration ---
CONFIG_FILE = 'config.ini'

# --- Logger Setup ---
def setup_logger(name, log_file, level=logging.INFO):
    """
    Sets up a custom logger for each tunnel.
    Args:
        name (str): The name of the logger (e.g., 'tunnel_1_logger').
        log_file (str): The path to the log file.
        level (int): The logging level (e.g., logging.INFO).
    Returns:
        logging.Logger: The configured logger instance.
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False # Prevent messages from propagating to root logger
    return logger

# --- Tunnel Handler ---
async def handle_tunnel(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                        forward_ip: str, forward_port: int, logger: logging.Logger):
    """
    Handles a single client connection, forwarding traffic between the client and the destination.
    Args:
        reader (asyncio.StreamReader): The reader for the client connection.
        writer (asyncio.StreamWriter): The writer for the client connection.
        forward_ip (str): The IP address of the destination.
        forward_port (int): The port of the destination.
        logger (logging.Logger): The logger for this specific tunnel.
    """
    client_addr = writer.get_extra_info('peername')
    logger.info(f"[{forward_ip}:{forward_port}] New client connected from {client_addr}")

    destination_reader = None
    destination_writer = None

    try:
        # Establish connection to the destination
        destination_reader, destination_writer = await asyncio.open_connection(forward_ip, forward_port)
        logger.info(f"[{forward_ip}:{forward_port}] Connected to destination {forward_ip}:{forward_port}")

        # Function to transfer data in one direction
        async def transfer_data(src_reader, dest_writer, direction_name):
            """
            Continuously reads data from src_reader and writes it to dest_writer.
            Logs the transferred data.
            """
            while True:
                try:
                    data = await src_reader.read(4096)  # Read up to 4KB of data
                    if not data:
                        logger.info(f"[{forward_ip}:{forward_port}] {direction_name}: No more data. Connection closed.")
                        break
                    dest_writer.write(data)
                    await dest_writer.drain() # Ensure data is sent
                    logger.debug(f"[{forward_ip}:{forward_port}] {direction_name}: Transferred {len(data)} bytes. Data: {data.hex()}")
                except ConnectionResetError:
                    logger.warning(f"[{forward_ip}:{forward_port}] {direction_name}: Connection reset by peer.")
                    break
                except Exception as e:
                    logger.error(f"[{forward_ip}:{forward_port}] {direction_name}: Error during transfer: {e}")
                    break

        # Create two tasks to transfer data concurrently in both directions
        task_client_to_dest = asyncio.create_task(transfer_data(reader, destination_writer, "Client -> Destination"))
        task_dest_to_client = asyncio.create_task(transfer_data(destination_reader, writer, "Destination -> Client"))

        # Wait for both tasks to complete (i.e., one of the connections closes)
        await asyncio.gather(task_client_to_dest, task_dest_to_client)

    except socket.gaierror as e:
        logger.error(f"[{forward_ip}:{forward_port}] Could not resolve destination IP '{forward_ip}': {e}")
    except ConnectionRefusedError:
        logger.error(f"[{forward_ip}:{forward_port}] Connection to destination {forward_ip}:{forward_port} refused.")
    except Exception as e:
        logger.error(f"[{forward_ip}:{forward_port}] An unexpected error occurred: {e}")
    finally:
        # Close all connections gracefully
        if writer:
            writer.close()
            await writer.wait_closed()
            logger.info(f"[{forward_ip}:{forward_port}] Client connection {client_addr} closed.")
        if destination_writer:
            destination_writer.close()
            await destination_writer.wait_closed()
            logger.info(f"[{forward_ip}:{forward_port}] Destination connection {forward_ip}:{forward_port} closed.")

# --- Main Gateway Logic ---
async def main():
    """
    Reads configuration, sets up and starts all configured tunnels.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please create it with tunnel configurations.")
        return

    config.read(CONFIG_FILE)

    tasks = []
    print(f"Loading tunnels from {CONFIG_FILE}...")

    for section in config.sections():
        try:
            listen_ip = config.get(section, 'listen_ip')
            listen_port = config.getint(section, 'listen_port')
            forward_ip = config.get(section, 'forward_ip')
            forward_port = config.getint(section, 'forward_port')
            log_file = config.get(section, 'log_file')

            # Ensure log directory exists if path is relative
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            tunnel_logger = setup_logger(section, log_file)
            tunnel_logger.info(f"Initializing tunnel: Listen on {listen_ip}:{listen_port}, Forward to {forward_ip}:{forward_port}")

            # Create an asyncio server for each tunnel
            server = await asyncio.start_server(
                lambda r, w, fw_ip=forward_ip, fw_port=forward_port, log=tunnel_logger:
                    handle_tunnel(r, w, fw_ip, fw_port, log),
                listen_ip,
                listen_port
            )
            addr = server.sockets[0].getsockname()
            print(f"Started {section} server on {addr}")
            tasks.append(server.serve_forever())

        except configparser.NoOptionError as e:
            print(f"Error in section [{section}]: Missing configuration option: {e}")
        except ValueError as e:
            print(f"Error in section [{section}]: Invalid value for option: {e}")
        except OSError as e:
            print(f"Error starting server for [{section}] on {listen_ip}:{listen_port}: {e}")
        except Exception as e:
            print(f"An unhandled error occurred while setting up tunnel [{section}]: {e}")

    if tasks:
        print("\nGateway is running. Press Ctrl+C to stop.")
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("Gateway stopped.")
        finally:
            for task in tasks:
                task.cancel() # Ensure all tasks are properly cancelled on exit
            await asyncio.gather(*tasks, return_exceptions=True) # Wait for tasks to clean up
    else:
        print("No tunnels configured or failed to start.")

# --- Entry Point ---
if __name__ == "__main__":
    # Basic console logging for the main process
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGateway shutdown initiated by user.")
