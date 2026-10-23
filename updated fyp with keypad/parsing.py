import os
import asyncio
import hashlib
from pathlib import Path
from llama_cloud import AsyncLlamaCloud

DATA_FOLDER = Path("./data")
CACHE_FOLDER = Path("./cache")
CACHE_FOLDER.mkdir(exist_ok=True)

SUPPORTED_EXTS = [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".xlsx"]
TIER = "agentic"
VERSION = "latest"

def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

async def process_single_file(file: Path, client: AsyncLlamaCloud):
    file_hash = get_file_hash(file)
    cache_path = CACHE_FOLDER / f"{file_hash}.md"

    if cache_path.exists():
        print(f"-> Cache HIT for {file.name}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    print(f"-> Cache MISS for {file.name}. Sending to cloud...")
    try:
        parse_result = await client.parsing.parse(
            upload_file=file,
            tier=TIER,
            version=VERSION,
            expand=["markdown_full"]
        )
        text = parse_result.markdown_full or parse_result.text_full
        if not text:
            return None

        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text

    except Exception as e:
        print(f"Error parsing file {file.name}: {e}")
        return None

async def parse_all_files(client: AsyncLlamaCloud):
    tasks = []
    for file in DATA_FOLDER.glob("*"):
        if file.suffix.lower() not in SUPPORTED_EXTS:
            continue
        tasks.append(process_single_file(file, client))

    results = await asyncio.gather(*tasks)
    combined_markdown = "\n\n---\n\n".join([text for text in results if text is not None])
    return combined_markdown