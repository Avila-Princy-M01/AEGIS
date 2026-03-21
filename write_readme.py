import pathlib

readme = pathlib.Path("README.md")
readme.write_text(open("readme_content.txt", encoding="utf-8").read(), encoding="utf-8")
print(f"README.md written: {len(readme.read_text(encoding='utf-8'))} chars")
