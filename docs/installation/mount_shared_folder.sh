#!/bin/bash
set -x
set -e

# you need to define the names and paths here
ideal_remote="//servername.domainname/path/to/IDEAL/folder"
ideal_rw="/var/data/IDEAL/io/IDEAL_rw"
ideal_ro="/var/data/IDEAL/io/IDEAL_ro"
creds="/var/data/IDEAL/io/secrets.txt"

for d in "$ideal_rw" "$ideal_ro"; do
	if [ ! -d "$d" ] ; then
		mkdir -p "$d"
	fi
done

# you need to provide the actual uid and gid here
creds_uid_gid="credentials=$creds,uid=montecarlo,gid=montecarlo"

rw_opts="-o rw,file_mode=0660,dir_mode=0770,$creds_uid_gid"
ro_opts="-o ro,file_mode=0440,dir_mode=0550,$creds_uid_gid"
sudo mount.cifs "$ideal_remote" "$ideal_rw" $rw_opts
sudo mount.cifs "$ideal_remote" "$ideal_ro" $ro_opts

