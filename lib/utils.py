import re

# Credits: http://stackoverflow.com/questions/1714027/version-number-comparison
def compare_version(version1, version2):
    def normalize(v):
        v.replace("-", ".")
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return cmp(normalize(version1), normalize(version2))

SIZES = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
BYTES = 1024

def get_filesize_display(size):
    for suffix in SIZES:
        size /= BYTES
        if size < BYTES:
            return '{0:.1f} {1}'.format(size, suffix)