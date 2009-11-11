#!/bin/sh -e

# Found at /oldroot/oldroot/usr/lib/udev/migrate-fstab-to-uuid.sh -- doesn't seem to exist in newer versions of Ubuntu. Looks like it was part of edgy upgrade. --Tyler
#    echo "# $DEV -- converted during upgrade to edgy"

# Rewrite /etc/fstab so that filesystems are mounted by UUID

if [ -e /etc/fstab.pre-uuid ]; then
    echo "/etc/fstab.pre-uuid already exists" 1>&2
    echo "remove this file before running the script again" 1>&2
    exit 1
fi

cp -a /etc/fstab /etc/fstab.pre-uuid
exec 9<&0 8>&1 </etc/fstab >/etc/fstab.new
trap "rm -f /etc/fstab.new" 0

uuids=""

old_IFS="$IFS"
IFS="
"
while read LINE
do
    IFS="$old_IFS"
    set -- $LINE
    IFS="
"
    DEV=$1 MTPT=$2 FSTYPE=$3 OPTS=$4

    # Check the device is sane for conversion
    case "$DEV" in
	""|\#*)		# Preserve blank lines and user comments
	    echo "$LINE"
	    continue
	    ;;
	LABEL=*|UUID=*)	# Already mounting by LABEL or UUID
	    echo "$LINE"
	    continue
	    ;;
	/dev/mapper/*_crypt)# DM-Crypt devices
	    echo "$LINE"
	    continue
	    ;;
	/dev/disk/*)	# Already mounting by particulars
	    echo "$LINE"
	    continue
	    ;;
	/dev/fd[0-9]*)	# Floppy devices, not mounted by filesystem
	    echo "$LINE"
	    continue
	    ;;
	/dev/*)		# Ordinary devices -- we want to convert
	    if [ ! -b "$DEV" ]; then
		echo "$LINE"
		continue
	    fi
	    ;;
	*)			# Anything else gets left alone
	    echo "$LINE"
	    continue
	    ;;
    esac 
    
    # Don't convert filesystem types that don't make sense
    case "$FSTYPE" in
	auto)		# Auto detection -- implies non-fixed fs
	    echo "$LINE"
	    continue
	    ;;
    esac
    
    # Check filesystem options also
    case "$OPTS" in
	noauto|*,noauto|noauto,*|*,noauto,*)	# Implies non-fixed
	    echo "$LINE"
	    continue
	    ;;
    esac


    # If we reach this point, we think we want to move the fstab
    # entry over to mount-by-UUID.  The first check is that the
    # filesystem on the device *has* a uuid
    UUID=$(/sbin/vol_id -u "$DEV" || true)
    if [ -z "$UUID" ]; then
	# Can we generate one?
	if [ "$FSTYPE" = "swap" ]; then
	    REAL_FSTYPE=$(/sbin/vol_id -t "$DEV" || true)
	    case "$REAL_FSTYPE" in
		swap)	# is a swap device, add a UUID to it
		    UUID=$(uuidgen)
		    echo -n "$UUID" |
		      perl -ne 's/-//g;chomp;print pack "H*",$_' |
		      dd conv=notrunc "of=$DEV" obs=1 seek=1036 2>/dev/null
		    ;;
		swsusp)	# contains a suspended image, mkswap it!
		    if ! mkswap "$DEV" >/dev/null; then
			echo "Warning: unable to make swap $DEV" 1>&2
			echo "$LINE"
			continue
		    fi

		    UUID=$(/sbin/vol_id -u "$DEV" || true)
		    if [ -z "$UUID" ]; then
			echo "Warning: unable to generate uuid for $DEV" 1>&2
			echo "$LINE"
			continue
		    fi
		    ;;
		*)
		    echo "Warning: $DEV is not a swap partition" 1>&2
		    echo "$LINE"
		    continue
		    ;;
	    esac
	else
	    echo "Warning: unable to find a UUID for $DEV" 1>&2
	    echo "$LINE"
	    continue
	fi
    fi

    # Check for duplicates
    case "$uuids" in
    "$UUID" | "$UUID "* | *" $UUID" | *" $UUID "*)
	echo "Error: duplicate UUID $UUID detected" 1>&2
	echo "Unable to migrate /etc/fstab to UUID-based mounting" 1>&2

	exec 0<&9 9<&- 1>&8 8>&-
	trap 0

	rm -f /etc/fstab.new
	exit 1
	;;
    *)
	uuids="${uuids:+$uuids }$UUID"
	;;
    esac

    # Now write the new line out
    shift
    echo "# $DEV -- converted during upgrade to edgy"
    echo "UUID=$UUID $@"
done
IFS="$old_IFS"

exec 0<&9 9<&- 1>&8 8>&-
trap 0

mv -f /etc/fstab.new /etc/fstab

exit 0
