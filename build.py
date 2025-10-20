
PROJECT_NAME = "kmake"
PROJECT_TYPE = "binary"
PROJECT_LANGUAGE = "C++"
PROJECT_LANGUAGE_STANDARD = "20"
PROJECT_COMPILER = "clang"
PROJECT_PLATFORM = "x64-windows"
PROJECT_STRUCTURE = {
    "kmakelib" : {
        "type" : "static-library",
        "deps" : {
            "lua" : {
                "type" : "static-library"
            },

        }
    },
    "kmake" : {
        "type" : "binary",
        "deps" : {
            "kmakelib" : {},
            "lua" : {
                "type" : "static-library"
            },        
            "sol2" : {
                "type" : "header-only-library"
            }
        }
    }
}