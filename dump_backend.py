import os
from pathlib import Path

def dump_backend():
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir / "backend"
    output_file = script_dir / "backendDump.txt"
    
    if not backend_dir.exists() or not backend_dir.is_dir():
        print(f"Error: 'backend' directory not found at {backend_dir}")
        return
        
    print(f"Scanning directory: {backend_dir}")
    print(f"Writing to: {output_file}")
    
    # Exclude directories
    exclude_dirs = {"target", ".git", ".mvn", ".vscode", ".idea", "build"}
    # Target extensions
    target_extensions = {".java", ".xml", ".properties", ".yml", ".yaml"}
    # Custom files to explicitly include/exclude
    exclude_files = {".env", ".gitignore", "mvnw", "mvnw.cmd"}
    
    dumped_count = 0
    
    with open(output_file, "w", encoding="utf-8") as outfile:
        # Walk directories
        for root, dirs, files in os.walk(backend_dir):
            # Prune directories in place to stop recursion
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in sorted(files):
                file_path = Path(root) / file
                file_ext = file_path.suffix.lower()
                file_name = file_path.name.lower()
                
                # Check inclusion criteria
                is_target_ext = file_ext in target_extensions or file_name == "pom.xml"
                is_excluded = file_name in exclude_files
                
                if is_target_ext and not is_excluded:
                    rel_path = file_path.resolve().relative_to(script_dir)
                    
                    outfile.write(f"// {'=' * 78}\n")
                    outfile.write(f"// File: {rel_path.as_posix()}\n")
                    outfile.write(f"// {'=' * 78}\n\n")
                    
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="replace") as infile:
                            content = infile.read()
                        outfile.write(content)
                        dumped_count += 1
                        print(f"Dumped: {rel_path}")
                    except Exception as e:
                        outfile.write(f"// Error reading file {rel_path}: {e}\n")
                        print(f"Error reading {rel_path}: {e}")
                        
                    outfile.write("\n\n")
                    
    print(f"\nSuccessfully dumped {dumped_count} backend file(s) into {output_file.name}")

if __name__ == "__main__":
    dump_backend()
