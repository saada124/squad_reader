import struct
from typing import Tuple

class FBChunksContainer:
    """
    Handles Frostbite Engine FBCHUNKS save container parsing and serialization.
    Preserves container metadata, chunk GUIDs, and length descriptors.
    """
    MAGIC = b"FBCHUNKS"
    HEADER_SIZE = 0xFA # 250 bytes
    DB_OFFSET = 0xFE   # 254 bytes
    
    def __init__(self):
        self.container_header = bytearray()
        self.version = 1
        self.header_len = 184
        self.db_payload = bytearray()
        self.guid = bytes(16)
        
    def load(self, filepath: str) -> bytearray:
        """Loads and validates a Squads file, extracting the inner DB payload."""
        with open(filepath, "rb") as f:
            data = f.read()
            
        if len(data) < self.DB_OFFSET:
            raise ValueError(f"File too small ({len(data)} bytes) to be a valid Squads save.")
            
        magic = data[:8]
        if magic != self.MAGIC:
            raise ValueError(f"Invalid header magic: {magic!r}, expected {self.MAGIC!r}")
            
        self.version, self.header_len, payload_len = struct.unpack("<HII", data[8:18])
        self.container_header = bytearray(data[:self.HEADER_SIZE])
        self.guid = bytes(data[0x54:0x64])
        
        # Verify internal DB size field at 0xFA
        internal_size = struct.unpack("<I", data[0xFA:0xFE])[0]
        self.db_payload = bytearray(data[self.DB_OFFSET:self.DB_OFFSET + internal_size])
        
        # Verify inner DB magic
        if self.db_payload[:4] != b"DB\x00\x08":
            raise ValueError(f"Invalid inner DB magic: {self.db_payload[:4]!r}")
            
        return self.db_payload

    def repack(self, modified_db_payload: bytes, output_filepath: str):
        """
        Repacks the modified database payload into the exact FBCHUNKS container format.
        Preserves all container headers and chunk GUIDs.
        """
        out = bytearray()
        hdr = bytearray(self.container_header)
        
        # Update container payload length at offset 14 (payload size + 52 bytes meta)
        total_container_payload = len(modified_db_payload) + 52
        struct.pack_into("<I", hdr, 14, total_container_payload)
        
        out.extend(hdr)
        # Offset 0xFA: internal payload size (4 bytes)
        out.extend(struct.pack("<I", len(modified_db_payload)))
        # Offset 0xFE: inner DB payload
        out.extend(modified_db_payload)
        
        with open(output_filepath, "wb") as f:
            f.write(out)
            
        return len(out)
