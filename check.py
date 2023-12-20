import hashlib
import os
import json
import sys

if len(sys.argv) != 2:
    print("Usage : python check.py <target directory>")
    exit()

target_dir = sys.argv[1]

def generate_sha256_hash(path):
    file1 = open(path)
    data = file1.read()
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def getEntryByPath(path,tree):
    pathComponents = path.split('/')
    for i in range(1,len(pathComponents)):
        for entry in tree:
            if entry['type'] == 'dir' and entry['path'] == '/'.join(pathComponents[:i+1]):
                if entry['path'] == path:
                    return entry
                if entry['directory'] is not None:
                    tree = entry['directory']
                    break

def generate_hash_tree_file(target):
    try:
        tree_file = open('.hash_tree.json','r')
        old_hash_tree = json.load(tree_file)
    except FileNotFoundError:
        old_hash_tree = None
    
    hash_tree = []
        
    for (root,dirs,files) in os.walk(target_dir, topdown=True):
        for dir in dirs:
            if root == target_dir:
                hash_tree.append({'type':'dir','path':root+'/'+dir,'hash':None,'directory':None})
            else:
                entry = getEntryByPath(root,hash_tree)
                if entry['directory'] is None:
                    entry['directory'] = [{'type':'dir','path':root+'/'+dir,'hash':None,'directory':None}]
                else:
                    entry['directory'].append({'type':'dir','path':root+'/'+dir,'hash':None,'directory':None})

        for file in files:
            if root == target_dir:
                hash_tree.append({'type':'file','path':root+'/'+file,'hash':generate_sha256_hash(root+'/'+file),'directory':None})
            else:
                entry = getEntryByPath(root,hash_tree)
                if entry['directory'] is None:
                    entry['directory'] = [{'type':'file','path':root+'/'+file,'hash':generate_sha256_hash(root+'/'+file),'directory':None}]
                else:
                    entry['directory'].append({'type':'file','path':root+'/'+file,'hash':generate_sha256_hash(root+'/'+file),'directory':None})  

    tree_file = open('.hash_tree.json','w')
    json.dump(hash_tree,tree_file)
    tree_file.close()
    return hash_tree,old_hash_tree

def checkNameinDirectory(name,tree):
    if tree==None:
        return False
    for item in tree:
        if item['path'] == name:
            return True
    return False

changes = []

def traverse_and_verify(new_tree,old_tree):
    global changes

    if old_tree is not None:
        for i in range(len(old_tree)):
            if not checkNameinDirectory(old_tree[i]['path'], new_tree):
                changes.append(('deleted',old_tree[i]['path']))
            
    if new_tree is not None:
        for i in range(len(new_tree)):
            old_entry = None

            if not checkNameinDirectory(new_tree[i]['path'], old_tree):
                changes.append(('added',new_tree[i]['path']))
                
                if new_tree[i]['type'] == 'dir':
                    traverse_and_verify(new_tree[i]['directory'],None)
                
                continue
            
            for entry in old_tree:
                if entry['path'] == new_tree[i]['path']:
                    old_entry = entry

        
            if new_tree[i]['type'] == 'file':            
                if new_tree[i]['hash'] != old_entry['hash']:
                    changes.append(('modified',new_tree[i]['path']))
            
            elif new_tree[i]['type'] == 'dir':
                traverse_and_verify(new_tree[i]['directory'],old_entry['directory'])


def checkChanges(target_dir):
    global changes
    changes=[]
    new_hash_tree,old_hash_tree = generate_hash_tree_file(target_dir)
    traverse_and_verify(new_hash_tree,old_hash_tree)
    return changes

changes = checkChanges(target_dir)

for change in changes : 
    print(change[0]+" : "+change[1])