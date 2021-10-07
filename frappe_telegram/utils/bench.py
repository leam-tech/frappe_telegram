import os
from frappe.utils import get_bench_path, get_site_path  # noqa


def get_bench_name():
    return os.path.basename(os.path.abspath(get_bench_path()))
