#! /bin/bash

# Uploading and committing annotations to the annotations repository.
#
# Expects there to be a local version of
# https://github.com/clamsproject/clams-aapb-annotations
#
# This doesn't do a push at the moment, that is left as a manula step
#
# TODO: this is hardly user-friendly, maybe add this to the CLAMS Dashboard


task="nel"

function print_help () {
    echo "Usage:"
    echo "$ run.sh -h                            print help message"
    echo "$ run.sh -p PROJECT -f FILE -r REPO    copy annotations to repository"
    echo "$ run.sh -c -r REPO [-m MESSAGE]       commit annotations to repository"
}


while getopts :p:f:r:m:ch option; do
    case ${option} in
	c) commit=true;;
	p) project=${OPTARG};;
	f) file=${OPTARG};;
	r) repo=${OPTARG};;
	m) message=${OPTARG};;
	h) print_help; exit;;
	*) echo "Illegal option -${OPTARG}"; print_help; exit;;
    esac
done

if [ ! -z "$project" ] && [ ! -z $file ] && [ ! -z $repo ];
then
    echo ">>> copying file to uploads directory..."
    # creating directories if needed
    dir1=$repo/uploads/$task
    dir2=$repo/uploads/$task/projects
    dir3=$repo/uploads/$task/projects/$project
    for dir in $dir1 $dir2 $dir3;
    do
	echo "$ mkdir $dir"
	[[ ! -d $dir ]] && mkdir $dir
    done
    # copy the annotation file
    echo "$ cp $file $repo/uploads/$task/projects/$project"
    cp $file $repo/uploads/$task/projects/$project
    exit
fi

if [ ! -z "$commit" ] && [ ! -z $repo ];
then
    echo ">>> committing changes in $repo"
    # first check whether there is a message, using default if not
    default_message="Uploading annotations for the Named Entity Linking task"
    if [ -z $message ]; then message=$default_message; fi
    # commit all changes, should possibly be updated so you select files
    # now it will stage files in the projects directory, but it will not
    # check for already staged files and thos will be commited as well
    cd $repo
    git checkout main
    echo "$ git add uploads/$task/projects"
    git add uploads/$task/projects
    git status -s
    pwd
    echo "Commit annotations in uploads/$task/projects? (y/n)"
    read reply
    if [ -z $reply ]; then echo "Aborted..."; exit; fi
    if [ $reply == 'y' ]; then
	echo "$ git commit -m '$message'"
	git commit -m "$message"
    else
	echo "Aborted..."
    fi
    exit
fi

echo "Nothing to do!"
print_help
