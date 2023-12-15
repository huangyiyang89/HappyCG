import os
import requests


def download_file(url, local_filename):
    with requests.get(url, stream=True) as response:
        with open(local_filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)


def main():
    local_file_path = "main.exe"
    remote_url = "http://box.huangyiyang.com/main.exe"

    # Check if local file exists
    if os.path.exists(local_file_path):
        # Get local file size
        local_file_size = os.path.getsize(local_file_path)

        # Get remote file size
        try:
            remote_file_size = int(requests.head(
                remote_url).headers["Content-Length"])
        except (requests.RequestException, KeyError):
            remote_file_size = None

        # Compare file sizes
        if local_file_size != remote_file_size:
            print("Downloading remote file...")
            download_file(remote_url, local_file_path)
            print("Download complete.")
        else:
            print("Local file is up to date.")
    else:
        print("Local file does not exist. Downloading remote file...")
        download_file(remote_url, local_file_path)
        print("Download complete.")

    # Run main.exe
    os.system(local_file_path)


if __name__ == "__main__":
    try:
        main()
    except Exception(''):
        input('按任意键退出')
