
### PARSER SETUP AND CONFIGURATION

re_next_float = re.compile("^[0-9]+\.?[0-9]*")
re_next_word = re.compile("^[^\s]+")
# OLD: re_next_quoted_word = re.compile('^"[^"]+"')
re_next_quoted_word = re.compile(r'^"(?:\\.|[^\\])*?"') # supports escapes
re_next_char_set = re.compile(r'^\[(?:\\.|[^\\])*?\]') # supports escapes


def parse(operation) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations without parameters."""

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        return (rest_of_op,operation)

    return parse_it   

def parse_only_static_parameters(operation_constructor) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations without a parameter. """

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        return (rest_of_op,operation_constructor())

    return parse_it

def parse_int_parameter(operation_constructor) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations with a single int parameter. """

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        int_match = re_next_word.match(rest_of_op)
        if not int_match:
           raise Exception(f"{op_name}: int parameter missing") 
        try:   
            raw_value = int_match.group(0)
            value = int(raw_value)
        except ValueError as ve:
            raise Exception(f"{op_name}: parameter {raw_value} is not an int") 
        new_rest_of_op = rest_of_op[int_match.end(0):].lstrip()
        return (new_rest_of_op,operation_constructor(value))

    return parse_it

def parse_float_parameter(operation_constructor) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations with a single float parameter. """

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        float_match = re_next_float.match(rest_of_op)
        if not float_match:
           raise Exception(f"{op_name}: float parameter missing") 
        try:   
            raw_value = float_match.group(0)
            value = float(raw_value)
        except ValueError as ve:
            raise Exception(f"{op_name}: parameter {raw_value} is not a float") 
        new_rest_of_op = rest_of_op[float_match.end(0):].lstrip()
        return (new_rest_of_op,operation_constructor(value))

    return parse_it

def parse_string(operation_constructor) -> Callable[[str,str],Tuple[str,Operation]]:
    """Generic parser for operations with a single unquoted string parameter. """

    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        string_match = re_next_word.match(rest_of_op)
        if not string_match:
           raise Exception(f"{op_name}: string parameter missing") 
        value = string_match.group(0)
        new_rest_of_op = rest_of_op[string_match.end(0):].lstrip()
        return (new_rest_of_op,operation_constructor(value))

    return parse_it

def parse_quoted_string(operation_constructor):
    """Generic parser for operations with a quoted parameter."""
    def parse_it(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
        string_match = re_next_quoted_word.match(rest_of_op)
        if not string_match:
            raise Exception(f"{op_name}: empty match (did you forgot the quotes?)")
        string = string_match.\
            group(0).\
            strip("\"").\
            replace("\\\"","\"").\
            replace("\\\\","\\")
        new_rest_of_op = rest_of_op[string_match.end(0):].lstrip()        
        return (new_rest_of_op,operation_constructor(string))    

    return parse_it

def parse_number(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    chars_to_number_match = re_next_word.match(rest_of_op)
    raw_chars_to_number = chars_to_number_match.group(0)
    chars_to_number = unescape(raw_chars_to_number)
    new_rest_of_op = rest_of_op[chars_to_number_match.end(0):].lstrip()
    return (new_rest_of_op,Number(chars_to_number[1:-1] ))


def parse_map(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    source_char_match = re_next_word.match(rest_of_op)
    raw_source_char = source_char_match.group(0)
    source_char = unescape(raw_source_char)
    rest_of_op = rest_of_op[source_char_match.end(0):].lstrip()

    target_chars_match = re_next_word.match(rest_of_op)
    raw_target_chars = target_chars_match.group(0)
    target_chars = unescape(raw_target_chars)
    new_rest_of_op = rest_of_op[target_chars_match.end(0):].lstrip()

    # TODO make parse set...
    return (new_rest_of_op,Map(source_char,target_chars[1:-1]))    

def parse_min(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    min_op_match = re_next_word.match(rest_of_op)
    raw_min_op = min_op_match.group(0)
    min_op = unescape(raw_min_op)
    rest_of_op = rest_of_op[min_op_match.end(0):].lstrip()

    int_match = re_next_word.match(rest_of_op)
    if not int_match:
        raise Exception(f"{op_name}: int parameter missing") 
    try:   
        raw_min_count = int_match.group(0)
        min_count = int(raw_min_count)
    except ValueError as ve:
        raise Exception(f"{op_name}: parameter {raw_min_count} is not an int") 
    rest_of_op = rest_of_op[int_match.end(0):].lstrip()
    return (rest_of_op,Min(min_op,min_count))    

def parse_split(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    split_chars_match = re_next_word.match(rest_of_op)
    raw_split_chars = split_chars_match.group(0)
    split_char = unescape(raw_split_chars)
    new_rest_of_op = rest_of_op[split_chars_match.end(0):].lstrip()
    return (new_rest_of_op,Split(split_char))

def parse_sub_splits(op_name: str, rest_of_op: str) -> Tuple[str, Operation]:
    split_chars_match = re_next_word.match(rest_of_op)
    raw_split_chars = split_chars_match.group(0)
    split_char = unescape(raw_split_chars)
    new_rest_of_op = rest_of_op[split_chars_match.end(0):].lstrip()
    return (new_rest_of_op,SubSplits(split_char))


macro_defs : Tuple[str,ComplexOperation] = { }


"""Mapping between the name of an op and it's associated parameters parser."""
operation_parsers = {

    "report" : parse(REPORT),
    "write" : parse_quoted_string(Write),
    
    # FILTERS
    "min" : parse_min,
    "is_regular_word" : parse(IS_REGULAR_WORD),
    "is_popular_word" : parse(IS_POPULAR_WORD),
    "is_pattern" : parse(IS_PATTERN),
    "is_walk" : parse_only_static_parameters(IsWalk),
    "is_sc" : parse(IS_SC),
    "sieve" : parse_quoted_string(Sieve),

    # EXTRACTORS
    "get_numbers" : parse(GET_NO),
    "get_sc" : parse(GET_SC),
    "deduplicate" : parse(DEDUPLICATE),
    "deduplicate_reversed" : parse(DEDUPLICATE_REVERSED),
    "detriplicate" : parse(DETRIPLICATE),
    "segments" : parse_int_parameter(Segments),

    # TRANSFORMERS
    "reverse" : parse(REVERSE),
    "fold_ws" : parse(FOLD_WS),
    "lower" : parse(LOWER),
    "upper" : parse(UPPER),
    "remove_numbers" : parse(REMOVE_NO),
    "remove_ws" : parse(REMOVE_WS),
    "remove_sc" : parse(REMOVE_SC),
    "capitalize" : parse(CAPITALIZE),
    "deleetify" : parse(DELEETIFY),
    "strip_ws" : parse(STRIP_WS),
    "strip_numbers_and_sc" : parse(STRIP_NO_AND_SC),
    "mangle_dates" : parse(MANGLE_DATES),
    "number" : parse_number,
    "map" : parse_map,
    "pos_map" : parse_quoted_string(PosMap),
    "related" : parse_float_parameter(Related),
    "split" : parse_split,
    "sub_splits" : parse_sub_splits,
    "replace" : parse_quoted_string(Replace),
    "discard_endings" : parse_quoted_string(DiscardEndings),
    "correct_spelling" : parse(CORRECT_SPELLING),
}


def parse_rest_of_op(previous_ops : List[Operation], line_number, rest_of_op : str) -> Tuple[str, Operation]:
    # Get name of operation parser
    next_op_parser_match = re_next_word.match(rest_of_op)
    next_op_parser_name = next_op_parser_match.group(0)

    # Check for operation modifiers (i.e. Metaoperations)
    keep_always = (next_op_parser_name[0] == "+")                
    keep_if_filtered = (next_op_parser_name[0] == "*") 
    negate_filter = (next_op_parser_name[0] == "!") 
    if keep_always or keep_if_filtered or negate_filter:
        next_op_parser_name = next_op_parser_name[1:]

    result : Tuple[str, Operation] = None

    if next_op_parser_name[0] == ">":
        if next_op_parser_name.startswith(">>"):
            set_name = next_op_parser_name[2:]
            store_filtered = False
        elif next_op_parser_name.startswith(">!>"):
            set_name = next_op_parser_name[3:]
            store_filtered = True
        else:
            print(
                f"[error][{line_number}] unsupported redirection command: {next_op_parser_name}", 
                file=stderr
            )
            return None
        if sets.get(set_name) is None:
            print(
                f"[error][{line_number}] unknown set: {set_name}", 
                file=stderr
            )
            return None
        new_rest_of_op = rest_of_op[next_op_parser_match.end(
                0):].lstrip()
        result = (new_rest_of_op, StoreInHeap(set_name,store_filtered))

    else:
        next_op_parser = operation_parsers.get(next_op_parser_name)
        if next_op_parser is not None:
            new_rest_of_op = rest_of_op[next_op_parser_match.end(
                0):].lstrip()
            result = next_op_parser(next_op_parser_name, new_rest_of_op)
        elif macro_defs.get(next_op_parser_name) is not None:
            macro_def = macro_defs.get(next_op_parser_name)
            new_rest_of_op = rest_of_op[next_op_parser_match.end(
                0):].lstrip()
            result = (
                new_rest_of_op,
                Macro(next_op_parser_name,macro_def.ops)
            )
        else:
            print(
                f"[error][{line_number}] unknown command: {next_op_parser_name}", 
                file=stderr
            )
            return None        

        if keep_always:
            (new_rest_of_op,base_op) = result
            result = (new_rest_of_op,KeepAlwaysModifier(base_op))
        elif keep_if_filtered:
            (new_rest_of_op,base_op) = result
            result = (new_rest_of_op,KeepOnlyIfFilteredModifier(base_op))
        elif negate_filter:
            (new_rest_of_op,base_op) = result
            result = (new_rest_of_op,NegateFilterModifier(base_op))

    return result
    

def parse_op(
        line_number : int, 
        is_def : bool, 
        sline : str
    ) -> ComplexOperation :
    # Parse a single operation definition in collaboration with the
    # respective atomic parsers.
    atomic_ops: List[Operation] = []
    while len(sline) > 0:
        parsed_atomic_op = parse_rest_of_op(atomic_ops, line_number, sline)
        if parsed_atomic_op:
            (sline, atomic_op) = parsed_atomic_op
            atomic_ops.append(atomic_op)
            if  not is_def and \
                len(sline) == 0 and \
                not (
                    isinstance(atomic_op,Report) 
                    or 
                    (   # ... a macro with a report at the end!
                        isinstance(atomic_op,Macro) 
                        and 
                        isinstance(atomic_op.ops[-1],Report)
                    )
                ):
                if _verbose:
                    print(f"[info][{line_number}] added missing report",  file=stderr)
                atomic_ops.append(Report())
        else:
            # If the parsing of an atomic operation fails, we just
            # ignore the line as a whole.
            print(f"[error][{line_number}] parsing failed: {sline}", file=stderr)
            return None

    return ComplexOperation(atomic_ops)


def parse_ops_file(ops_filename : str) -> List[ComplexOperation]:
    """ Parses a file containing operation definitions.
    """
    abs_filename = locate_resource(ops_filename)
    raw_lines : List[str] = []
    with open(abs_filename, 'r', encoding='utf-8') as ops_file:
        raw_lines = ops_file.readlines()

    return parse_ops(raw_lines)


def parse_ops(raw_lines : List[str]) -> List[ComplexOperation]:
    """ Parses operation definitions together with atomic operations parsers. 

        The split between the two kinds of parsers is as follows:
        This method parses global directives (`ignore`) and in all other
        cases it parses just the next word to determine the next atomic operation;
        the atomic operation is then responsible for parsing its parameters and
        removing them from the string.
    """
    ops: List[ComplexOperation] = []
    line_number = 0
    parsing_ops = False
    effective_lines = []
    current_line = ""
    for i in range (len(raw_lines)-1,0-1,-1):
        raw_line = raw_lines[i].rstrip("\r\n")
        if raw_line.startswith('\ '):
            current_line = raw_line[2:] + " " + current_line
        else:
            if len(current_line) > 0:
                effective_lines.append(raw_line + " " + current_line)
            else:
                effective_lines.append(raw_line)
            current_line = ""
    effective_lines.reverse()

    for op_def in effective_lines:
        line_number = line_number + 1
        sline = op_def.strip()

        # ignore comments and empty lines
        if sline.startswith('#') or len(sline) == 0:
            continue

        # parse ignore statement
        elif sline.startswith("ignore"):
            if parsing_ops:
                raise IllegalStateError(
                    f"ignore statements ({sline}) have to be defined before operation definitions"
                )

            filename = get_filename(sline[len("ignore")+1:].strip())
            abs_filename = locate_resource(filename)
            with open(abs_filename, 'r', encoding='utf-8') as fin:
                for ignore_entry in fin:
                    # We want to be able to strip words with spaces
                    # at the beginning or end.
                    stripped_ignore_entry = ignore_entry.rstrip("\r\n")
                    if len(stripped_ignore_entry) > 0:
                        ignored_entries.add(stripped_ignore_entry)

        # parse macro definitions
        elif sline.startswith("def"):
            macro_def = sline[len("def")+1:]
            macro_name_match = re_next_word.match(macro_def)
            macro_name = macro_name_match.group(0)
            macro_body = macro_def[macro_name_match.end(0):].lstrip()
            if macro_name.upper() != macro_name:
                raise ValueError(f"macro names need to be upper case: {macro_name}")
            op = parse_op(line_number, True, macro_body)
            if op:
                if macro_defs.get(macro_name):
                    raise IllegalStateError(f"macro ({macro_name}) already defined")
                else:
                    macro_defs[macro_name] = op

        elif sline.startswith("set"):
            set_def = sline[len("set")+1:]            
            set_name_match = re_next_word.match(set_def)
            set_name = set_name_match.group(0)
            if set_name.upper() != set_name:
                raise ValueError(f"set names need to be upper case: {set_name}")
            if sets.get(set_name):
                raise IllegalStateError(f"set ({set_name}) already defined")
            else:
                sets[set_name] = {}     

        elif sline.startswith("config"):
            if parsing_ops:
                raise IllegalStateError(
                    f"config statements ({sline}) have to be defined before operation definitions"
                )

            raw_config = sline[len("config")+1:].split()
            if len(raw_config) != 3:
                raise ValueError(
                    f"invalid config: {raw_config} (expected format: <op-module> <field> <value>)"
                )
            (op_module_name,field_name,raw_value) = raw_config
            op_module = importlib.import_module("operations."+op_module_name)
            op_class_name = "".join(
                    map (lambda x: x.capitalize(), op_module_name.split("_"))
                )
            op_class = getattr(op_module,op_class_name)
            value = None
            try:
                old_value = getattr(op_class,field_name)
            except AttributeError:
                # we don't want to create "new" fields 
                raise ValueError(
                    f"unknown field name: {op_class_name}.{field_name}"
                )

            if _verbose:
                print(
                    f"[debug] config:"+
                    f"{op_module.__name__}.{op_class.__name__}.{field_name} = "+
                    f"{raw_value} (old:{old_value})",file=sys.stderr)


            value_type = type(old_value)
            if value_type == int:
                value = int(raw_value)
            elif value_type == bool:
                value = bool(raw_value)                
            elif value_type == float:
                value = float(raw_value)
            elif value_type == str:
                value = raw_value
            else:
                raise ValueError(
                    f"unknown type: {value_type}; expected: integer, float or strings"
                )
            setattr(op_class,field_name,value)


        # parse an operation definition
        else:
            parsing_ops = True
            try:
                op = parse_op(line_number, False, sline)
                if op:
                    ops.append(op)
            except ValueError as ve:
                print(
                    f"failed parsing:\n\t{sline}\n\t{ve.args[0]}\n\tparsing aborted",
                    file=sys.stderr
                )
                return []

    return ops