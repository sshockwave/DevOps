from pathlib import Path

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(prog='arknights')
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        default='/mnt/c/Users/sshockwave/Downloads/output',
    )
    args = parser.parse_args()
    with open(args.output / 'hot_update_list.json', 'r') as f:
        import json
        data = json.load(f)
    ver_key = 'versionId'
    print(data[ver_key])

if __name__=='__main__':
    main()
