import hashlib
import json
import os

def hash_content(content: str) -> str:
    """Hash string content using SHA-256."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def hash_file(path: str) -> str:
    """Hash a file using SHA-256."""
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def hash_dict(data: dict) -> str:
    """Hash a dictionary deterministically using SHA-256."""
    encoded = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()

def verify_witness_hash(witness_dict: dict) -> bool:
    """Verify the witness hash matches the hash of its other contents."""
    if 'witness_hash' not in witness_dict:
        return False
    provided_hash = witness_dict['witness_hash']
    # Create copy without witness_hash for computation
    data = dict(witness_dict)
    del data['witness_hash']
    computed_hash = hash_dict(data)
    return provided_hash == computed_hash
