import os
import re

def remove_emojis(text):
    # Regex for emojis and pictographs
    # This covers a wide range of unicode blocks used for emojis
    emoji_pattern = re.compile(
        "["
        "\\U0001f600-\\U0001f64f"  # Emoticons
        "\\U0001f300-\\U0001f5ff"  # Misc Symbols and Pictographs
        "\\U0001f680-\\U0001f6ff"  # Transport and Map
        "\\U0001f1e0-\\U0001f1ff"  # Flags (iOS)
        "\\U00002700-\\U000027bf"  # Dingbats
        "\\U00002600-\\U000026ff"  # Misc Symbols
        "\\U00002460-\\U000024ff"  # Enclosed Alphanumerics
        "\\U0001f900-\\U0001f9ff"  # Supplemental Symbols and Pictographs
        "\\U0001fa70-\\U0001faff"  # Symbols and Pictographs Extended-A
        "\\U0001f700-\\U0001f7ff"  # Geometric Shapes Extended (includes circles)
        "\\ufe0f"                  # Variation Selector-16
        "\\u200d"                  # Zero Width Joiner
        "\\u26a0"                  # Warning sign
        "\\u26a1"                  # High Voltage
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub("", text)

def purge_emojis_from_directory(root_dir):
    cleaned_count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip hidden directories and node_modules
        if 'node_modules' in dirpath or '.git' in dirpath or '__pycache__' in dirpath:
            continue
            
        for filename in filenames:
            if filename.endswith(('.py', '.md', '.json', '.ts', '.tsx', '.js', '.vsc', '.txt')):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = remove_emojis(content)
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Cleaned: {filepath}")
                        cleaned_count += 1
                except Exception as e:
                    print(f"Skipping {filepath}: {e}")
                    
    print(f"\nTotal files cleaned: {cleaned_count}")

if __name__ == "__main__":
    target_dir = os.getcwd()
    print(f"Starting Emoji Purge in {target_dir}...")
    purge_emojis_from_directory(target_dir)
