import re

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.formatters.utils.patches import create_patch


def custom_format(compilation_unit: SlitherCompilationUnit, result):
    for file_scope in compilation_unit.scopes.values():
        elements = result["elements"]
        for element in elements:
            target_contract = file_scope.get_contract_from_name(
                element["type_specific_fields"]["parent"]["name"]
            )
            if target_contract:
                function = target_contract.get_function_from_full_name(
                    element["type_specific_fields"]["signature"]
                )
                if function:
                    _patch(
                        file_scope,
                        result,
                        element["source_mapping"]["filename_absolute"],
                        int(function.parameters_src().source_mapping.start),
                        int(function.returns_src().source_mapping.start),
                    )


def _patch(
    compilation_unit: SlitherCompilationUnit, result, in_file, modify_loc_start, modify_loc_end
):
    in_file_str = compilation_unit.core.source_code[in_file].encode("utf8")
    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
    # Search for 'public' keyword which is in-between the function name and modifier name (if present)
    # regex: 'public' could have spaces around or be at the end of the line
    m = re.search(r"((\spublic)\s+)|(\spublic)$|(\)public)$", old_str_of_interest.decode("utf8"))
    if m is None:
        # No visibility specifier exists; public by default.
        create_patch(
            result,
            in_file,
            # start after the function definition's closing paranthesis
            modify_loc_start + len(old_str_of_interest.decode("utf8").split(")")[0]) + 1,
            # end is same as start because we insert the keyword `external` at that location
            modify_loc_start + len(old_str_of_interest.decode("utf8").split(")")[0]) + 1,
            "",
            " external",
        )  # replace_text is `external`
    else:
        create_patch(
            result,
            in_file,
            # start at the keyword `public`
            modify_loc_start + m.span()[0] + 1,
            # end after the keyword `public` = start + len('public'')
            modify_loc_start + m.span()[0] + 1 + len("public"),
            "public",
            "external",
        )
