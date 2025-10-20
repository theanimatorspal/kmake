
PROJECT_NAME = "kmake"
PROJECT_TYPE = "binary"
PROJECT_LANGUAGE = "C++"
PROJECT_LANGUAGE_STANDARD = "20"
PROJECT_COMPILER = "clang"
PROJECT_STRUCTURE = {
    "kmakelib" : {
        "type" : "static-library"
    },
    "kmake" : {
        "type" : "binary",
        "deps" : {
            "kmakelib"
        }
    }
}