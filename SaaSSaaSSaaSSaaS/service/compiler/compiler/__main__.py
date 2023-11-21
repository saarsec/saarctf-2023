def compile_sl(source):
    from .parse import parser
    from .compiler import Compiler

    ast = parser.parse(source)
    c = Compiler()
    return c.compile(ast)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("source_file")
    parser.add_argument("-o", "--output")

    args = parser.parse_args()
    with open(args.source_file) as f:
        code = f.read()

    binary = compile_sl(code)

    outfile = args.output or f"{args.source_file}.bin"
    with open(outfile, 'wb') as f:
        f.write(binary)


if __name__ == '__main__':
    main()
