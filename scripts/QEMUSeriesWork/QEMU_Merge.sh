#!/bin/bash

MERGE_SHA=359c41abe32638adad503e386969fa428cecff52

# Check the 'both modified' files
echo "### Check the 'both modified' files ###"
ALL_PATCHES="$(git status | grep "both" | cut -d " " -f 5)"; # This is messy, but works

for PATCH_PATH in ${ALL_PATCHES}; do
	echo "---- ${PATCH_PATH} ----"
	git log --pretty=format:"%s - %ae - %aE" ${MERGE_SHA}..HEAD -- ${PATCH_PATH} | grep -v "merge" | grep -v "Merge" | \
		grep -v "Update the header files based on mainline" | \
		grep "xilinx" > /dev/null
	if [ $? -eq 1 ]; then
		echo "    No Xilinx changes to file since last merge"
		git checkout ${MERGE_SHA} -- ${PATCH_PATH}
		continue
	fi
	# Is the log empty?
	if [ $(git log ${MERGE_SHA}..HEAD -- ${PATCH_PATH} | wc -l) -eq 0 ]; then
		echo "    No changes to file since last merge"
		git checkout ${MERGE_SHA} -- ${PATCH_PATH}
		continue
	fi

	git reset -- ${PATCH_PATH} > /dev/null
done

# Check the 'both added' files
echo "### Check the 'both added' files ###"
ALL_PATCHES="$(git status | grep "both" | cut -d " " -f 8)"; # This is messy, but works
for PATCH_PATH in ${ALL_PATCHES}; do
	echo "---- ${PATCH_PATH} ----"
	git log --pretty=format:"%s - %ae - %aE" ${MERGE_SHA}..HEAD -- ${PATCH_PATH} | grep -v "merge" | grep -v "Merge" | \
		grep -v "Update the header files based on mainline" | \
		grep "xilinx" > /dev/null
	if [ $? -eq 1 ]; then
		echo "    No Xilinx changes to file since last merge"
		git checkout ${MERGE_SHA} -- ${PATCH_PATH}
		continue
	fi
	# Is the log empty?
	if [ $(git log ${MERGE_SHA}..HEAD -- ${PATCH_PATH} | wc -l) -eq 0 ]; then
		echo "    No changes to file since last merge"
		git checkout ${MERGE_SHA} -- ${PATCH_PATH}
		continue
	fi

	git reset -- ${PATCH_PATH} > /dev/null
done
