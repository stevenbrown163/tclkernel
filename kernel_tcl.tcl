rename puts old_puts

proc puts {args} {
	if {[llength $args] == 1 || [lindex $args 0] == "stdout"} {
		set temp_file [open "temp.temp" a]
		old_puts $temp_file [lindex $args end]
		close $temp_file
	} else {
		old_puts {*}$args
	}
}
