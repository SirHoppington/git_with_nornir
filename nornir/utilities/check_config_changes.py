import os
import filecmp

# Compare the files in the golden directory and the proposed CRQ dir
def compare_changes(golden, proposed):
    files = []
    for file in os.listdir(f"{golden}/"):
        files.append(file)
    results = filecmp.cmpfiles(golden, proposed, files, shallow=True)
    hostnames = [os.path.splitext(x)[0] for x in results[1]]
    return hostnames

def main():
    compare_changes()

if __name__ == "__main__":
    main()
