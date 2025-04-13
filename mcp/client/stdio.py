import asyncio
import subprocess
from typing import Tuple, Optional, Any

class StdinStdoutStream:
    """
    A wrapper around stdin/stdout streams for communication with subprocess.
    """
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
    
    async def read(self, n: int = -1) -> bytes:
        """Read up to n bytes from the stream."""
        return await self.reader.read(n)
    
    async def readline(self) -> bytes:
        """Read a line from the stream."""
        return await self.reader.readline()
    
    async def write(self, data: bytes) -> None:
        """Write data to the stream."""
        self.writer.write(data)
        await self.writer.drain()
    
    async def aclose(self) -> None:
        """Close the stream."""
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except:
            pass

class StdioServerParameters:
    """
    Parameters for stdio server connection.
    """
    def __init__(self, process: Optional[subprocess.Popen] = None):
        self.process = process

async def stdio_client(params: StdioServerParameters) -> Tuple[StdinStdoutStream, StdinStdoutStream]:
    """
    Create a stdio client connection to the server process.
    
    Returns:
        A tuple of (stdin_stream, stdout_stream) for bidirectional communication.
    """
    if params.process is None:
        raise ValueError("Process must be provided")
    
    # Create stream readers and writers
    process = params.process
    
    # Create stdin stream (writing to process)
    stdin_writer = asyncio.StreamWriter(process.stdin, None, None, None)
    stdin_reader = asyncio.StreamReader()
    stdin_protocol = asyncio.StreamReaderProtocol(stdin_reader)
    
    # Create stdout stream (reading from process)
    stdout_reader = asyncio.StreamReader()
    stdout_protocol = asyncio.StreamReaderProtocol(stdout_reader)
    stdout_writer = asyncio.StreamWriter(process.stdout, None, None, None)
    
    # Create stream wrappers
    stdin_stream = StdinStdoutStream(stdin_reader, stdin_writer)
    stdout_stream = StdinStdoutStream(stdout_reader, stdout_writer)
    
    # Start reading from process stdout
    def pipe_data():
        while True:
            try:
                data = process.stdout.read(1)
                if not data:
                    break
                stdout_reader.feed_data(data)
            except (BrokenPipeError, ValueError):
                break
        stdout_reader.feed_eof()
    
    # Start the pipe data loop in a separate thread
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, pipe_data)
    
    return stdin_stream, stdout_stream
