antiSMASH abuse prevention queue cleaner
========================================
[![Build Status](https://github.drone.secondarymetabolites.org/api/badges/antismash/bouncer/status.svg)](https://github.drone.secondarymetabolites.org/antismash/bouncer)

A simple cleanup job that moves jobs from one of the throttled queues back to
the main queue if there are few enough jobs of a throttled user left.

License
-------

Under the same GNU AGPL v3 or later license as the rest of antiSMASH.
See [`LICENSE.txt`](LICENSE.txt) for details.
