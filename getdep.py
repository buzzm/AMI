import subprocess
import argparse
import re

#  com.google.guava guava 33.2.1-jre
#  

def get_mvndep(group_id, artifact_id, version):
    # Construct the Maven command
    mvn_command = [
        #"sh",
        #"/Users/buzz/codes/apache-maven-3.5.2/bin/mvn",
        "mvn",         # brew installed
        "-e",
        "dependency:tree",
        f"-DgroupId={group_id}",
        f"-DartifactId={artifact_id}",
        f"-Dversion={version}",
        "-DoutputType=text"
    ]

    mvn_command = [
        "sh",
        "/Users/buzz/bin/mvndep",
        group_id,
        artifact_id,
        version,
        'tgf'
    ]

    XXmvn_command = [
        "cat",
        "/tmp/z2"
    ]    
    
    # Run the Maven command and capture the output
    result = subprocess.run(mvn_command, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Error running Maven command: {result.stderr}")
    
    return result.stdout
    
            
    

def main():
    parser = argparse.ArgumentParser(description='Fetch and parse Maven dependencies.')
    parser.add_argument('groupId', type=str, help='Maven groupId')
    parser.add_argument('artifactId', type=str, help='Maven artifactId')
    parser.add_argument('version', type=str, help='Maven version')
    rargs = parser.parse_args()

    data = get_mvndep(rargs.groupId, rargs.artifactId, rargs.version)

    lines = data.splitlines()
    
    state = -1

    hh = {}
    
    for ll in lines:
        ll = ll[7:]

        # Throw away anything before TMP:TMP:
        if state == -1:
            if "TMP:TMP:jar" in ll:
                state = 0
            else:
                continue

        if '----' in ll:
            break  # all done

        if ll == '#':
            state = 1
            continue
        
        if state == 0:
            (key,name) = ll.split(' ')
            hh[key] = name
        elif state == 1:            
            (src,dest,context) = ll.split(' ')
            print("%s %s" % (hh[src],hh[dest]))

if __name__ == "__main__":        
    main()
        
