from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
rocksdb_target_header = """REPO_PATH = package_name() + "/"

BUCK_BINS = "buck-out/gen/" + REPO_PATH

TEST_RUNNER = REPO_PATH + "buckifier/rocks_test_runner.sh"

rocksdb_compiler_flags = [
    "-fno-builtin-memcmp",
    "-DROCKSDB_PLATFORM_POSIX",
    "-DROCKSDB_LIB_IO_POSIX",
    "-DROCKSDB_FALLOCATE_PRESENT",
    "-DROCKSDB_MALLOC_USABLE_SIZE",
    "-DROCKSDB_RANGESYNC_PRESENT",
    "-DROCKSDB_SCHED_GETCPU_PRESENT",
    "-DROCKSDB_SUPPORT_THREAD_LOCAL",
    "-DOS_LINUX",
    # Flags to enable libs we include
    "-DSNAPPY",
    "-DZLIB",
    "-DBZIP2",
    "-DLZ4",
    "-DZSTD",
    "-DGFLAGS=gflags",
    "-DNUMA",
    "-DTBB",
    # Needed to compile in fbcode
    "-Wno-expansion-to-defined",
]

rocksdb_external_deps = [
    ("bzip2", None, "bz2"),
    ("snappy", None, "snappy"),
    ("zlib", None, "z"),
    ("gflags", None, "gflags"),
    ("lz4", None, "lz4"),
    ("zstd", None),
    ("tbb", None),
    ("numa", None, "numa"),
    ("googletest", None, "gtest"),
]

rocksdb_preprocessor_flags = [
    # Directories with files for #include
    "-I" + REPO_PATH + "include/",
    "-I" + REPO_PATH,
]

rocksdb_arch_preprocessor_flags = {
    "x86_64": ["-DHAVE_SSE42"],
}

build_mode = read_config("fbcode", "build_mode")

is_opt_mode = build_mode.startswith("opt")

# -DNDEBUG is added by default in opt mode in fbcode. But adding it twice
# doesn't harm and avoid forgetting to add it.
if is_opt_mode:
    rocksdb_compiler_flags.append("-DNDEBUG")
"""


library_template = """
cpp_library(
    name = "%s",
    srcs = [%s],
    headers = %s,
    arch_preprocessor_flags = rocksdb_arch_preprocessor_flags,
    compiler_flags = rocksdb_compiler_flags,
    preprocessor_flags = rocksdb_preprocessor_flags,
    deps = [%s],
    external_deps = rocksdb_external_deps,
)
"""

binary_template = """
cpp_binary(
    name = "%s",
    srcs = [%s],
    arch_preprocessor_flags = rocksdb_arch_preprocessor_flags,
    compiler_flags = rocksdb_compiler_flags,
    preprocessor_flags = rocksdb_preprocessor_flags,
    deps = [%s],
    external_deps = rocksdb_external_deps,
)
"""

test_cfg_template = """    [
        "%s",
        "%s",
        "%s",
    ],
"""

unittests_template = """
# [test_name, test_src, test_type]
ROCKS_TESTS = [
%s]

# Generate a test rule for each entry in ROCKS_TESTS
# Do not build the tests in opt mode, since SyncPoint and other test code
# will not be included.
if not is_opt_mode:
    for test_cfg in ROCKS_TESTS:
        test_name = test_cfg[0]
        test_cc = test_cfg[1]
        ttype = "gtest" if test_cfg[2] == "parallel" else "simple"
        test_bin = test_name + "_bin"

        cpp_binary (
          name = test_bin,
          srcs = [test_cc],
          deps = [":rocksdb_test_lib"],
          preprocessor_flags = rocksdb_preprocessor_flags,
          arch_preprocessor_flags = rocksdb_arch_preprocessor_flags,
          compiler_flags = rocksdb_compiler_flags,
          external_deps = rocksdb_external_deps,
        )

        custom_unittest(
          name = test_name,
          type = ttype,
          deps = [":" + test_bin],
          command = [TEST_RUNNER, BUCK_BINS + test_bin]
        )

custom_unittest(
    name = "make_rocksdbjavastatic",
    command = ["internal_repo_rocksdb/make_rocksdbjavastatic.sh"],
    type = "simple",
)

custom_unittest(
    name = "make_rocksdb_lite_release",
    command = ["internal_repo_rocksdb/make_rocksdb_lite_release.sh"],
    type = "simple",
)
"""
