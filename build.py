
PROJECT_NAME = "kmake"
PROJECT_TYPE = "binary"
PROJECT_LANGUAGE = "C++"
PROJECT_LANGUAGE_STANDARD = "20"
PROJECT_COMPILER = "clang"
PROJECT_STANDARD_LIBRARY = "default"
PROJECT_PLATFORM = "x64-windows"
PROJECT_STRUCTURE = {
    "kmakelib" : {
        "type" : "static-library",
        "deps" : {
            "lua" : {
                "version" : "5.4.7"
            },
        }
    },
    "kmake" : {
        "type" : "binary",
        "deps" : {
            "kmakelib" : {},
            "lua" : {
                "version" : "5.4.7"
            },        
            "sol2" : {
                "version" : "3.5.0"
            }
        }
    }
}