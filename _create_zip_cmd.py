"""Create a zip.cmd wrapper for the agentcore CLI."""
import sys, os

scripts_dir = os.path.dirname(sys.executable)

# Create the zip wrapper
wrapper_py = os.path.join(scripts_dir, "_zip_wrapper.py")
with open(wrapper_py, "w") as f:
    f.write("""import sys, zipfile, os

args = sys.argv[1:]
recursive = '-r' in args
quiet = '-q' in args
exclude = []
filtered = []
i = 0
while i < len(args):
    if args[i] in ('-r', '-q'):
        i += 1
        continue
    if args[i] == '-x':
        i += 1
        while i < len(args) and not args[i].startswith('-'):
            exclude.append(args[i].replace('"','').replace("'",""))
            i += 1
        continue
    filtered.append(args[i])
    i += 1

outfile = filtered[0]
sources = filtered[1:]

with zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED) as zf:
    for src in sources:
        if os.path.isdir(src):
            for root, dirs, files in os.walk(src):
                for fn in files:
                    skip = False
                    for ex in exclude:
                        if fn.endswith(ex.replace('*','')):
                            skip = True
                    if skip:
                        continue
                    fp = os.path.join(root, fn)
                    arcname = os.path.relpath(fp, src)
                    zf.write(fp, arcname)
        elif os.path.isfile(src):
            zf.write(src, os.path.basename(src))

if not quiet:
    print(f'Created {outfile} ({os.path.getsize(outfile)} bytes)')
""")

cmd_file = os.path.join(scripts_dir, "zip.cmd")
with open(cmd_file, "w") as f:
    f.write(f'@python "{wrapper_py}" %*\n')

print(f"Created: {cmd_file}")
print(f"Testing: zip command available")
os.system(f'"{cmd_file}"')
