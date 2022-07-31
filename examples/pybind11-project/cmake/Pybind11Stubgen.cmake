function(pybind11_stubgen target)

    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    execute_process(COMMAND ${Python3_EXECUTABLE}
        -c "import os; print(os.pathsep)"
        OUTPUT_VARIABLE PY_PATH_SEP
        OUTPUT_STRIP_TRAILING_WHITESPACE)
    string(REPLACE ";" "\\;" PY_PATH_SEP "${PY_PATH_SEP}")
    set(PY_PATH "$<TARGET_FILE_DIR:${target}>${PY_PATH_SEP}$ENV{PYTHONPATH}")
    add_custom_command(TARGET ${target} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E env PYTHONPATH="${PY_PATH}"
            ${Python3_EXECUTABLE} -m pybind11_stubgen
                $<TARGET_FILE_BASE_NAME:${target}>
                --bare-numpy-ndarray
                --no-setup-py
                -o ${CMAKE_CURRENT_BINARY_DIR}
        WORKING_DIRECTORY $<TARGET_FILE_DIR:${target}>
        USES_TERMINAL)

endfunction()

function(pybind11_stubgen_install target destination)

    install(FILES ${CMAKE_CURRENT_BINARY_DIR}/$<TARGET_FILE_BASE_NAME:${target}>-stubs/__init__.pyi
        EXCLUDE_FROM_ALL
        COMPONENT python_modules
        RENAME $<TARGET_FILE_BASE_NAME:${target}>.pyi
        DESTINATION ${destination})

endfunction()