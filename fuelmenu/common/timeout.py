#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import signal

class TimeoutError(Exception):
    pass


def handler(signum, frame):
    raise TimeoutError('Timeout error')


def run_with_timeout(func, args=tuple(),
                     kwargs=None, timeout=60):
    """Run function and raise exception if case of timeout.

    Run function func and return what this function returned
    if the execution took no longer than timeout. If timeout
    exceeded function raises TimeoutError exception. If user
    pressed Ctrl-C during this function, it raises
    KeyboardInterrupt.
    """
    kwargs = kwargs or dict()
    if not timeout:
        return func(*args, **kwargs)

    signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        result = func(*args, **kwargs)
        return result
    finally:
        signal.alarm(0)
