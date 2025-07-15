import re

def convert_line(line):
    # If already in new format, return as is
    if line.strip().startswith('https://www.google.com/maps?q='):
        return line
    # Try to match old format: timestamp, ip, lat, lon
    match = re.match(r'([^,]+),\s*([^,]+),\s*([\d.]+),\s*([\d.]+)', line)
    if match:
        timestamp, ip, lat, lon = match.groups()
        url = f"https://www.google.com/maps?q={lat},{lon}  # {timestamp}, {ip}\n"
        return url
    return ''  # skip lines that don't match

def main():
    try:
        with open('locations.txt', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print('locations.txt not found.')
        return
    new_lines = [convert_line(line) for line in lines]
    new_lines = [l for l in new_lines if l]
    with open('locations.txt', 'w') as f:
        f.writelines(new_lines)
    print('locations.txt has been converted to the new format.')

if __name__ == '__main__':
    main() 