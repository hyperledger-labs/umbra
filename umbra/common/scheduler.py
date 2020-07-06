import logging
import asyncio
from datetime import datetime


logger = logging.getLogger(__name__)


class Handler:
    def _check_finish(self, uid, finish, timeout):
        """Checks if task has reached timeout
        
        Arguments:
            uid {string} -- Unique identifier of task
            finish {int} -- Time in seconds that task must end
            timeout {int} -- Time in seconds that task is taking
        
        Returns:
            bool -- A flag True if timeout is bigger than finish, False otherwise
        """
        if finish == 0:
            pass
        else:
            if finish <= timeout:
                logger.debug(f"Task {uid} finish timeout {timeout}")
                return True
            else:
                logger.debug(f"Task {uid} timeout {timeout}")
        return False

    async def _check_task(self, uid, task, duration):
        """Checks task if finished to obtain output result
        
        Arguments:
            uid {string} -- Unique identifier of call
            task {coroutine} -- Task coroutine of command call uid
            duration {int} -- Expected duration of task
        
        Returns:
            int -- Amount of time in seconds that task took to be executed
        """
        if duration != 0:
            logger.debug(f"Waiting for task {uid} duration")
            await asyncio.sleep(duration)
            logger.debug(f"Task {uid} duration ended")
            task_duration = duration
        else:
            logger.debug(f"Waiting for task {uid} (normal execution)")
            start = datetime.now()
            _, _ = await asyncio.wait({task})
            stop = datetime.now()
            task_duration = (stop - start).total_seconds()
        
        return task_duration

    async def _check_task_result(self, uid, task):
        """Retrieves task output result 
        
        Arguments:
            uid {string} -- Unique identifier of task/call
            task {coroutine} -- Task coroutine of command call uid
        
        Returns:
            dict -- Output of task command executed by call
        """
        logger.debug(f"Checking Task {uid}")
        if task.done():
            logger.debug(f"Result Task {uid} Done")
            result = task.result()
        else:
            logger.debug(f"Cancel Task {uid} Pending")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug(f"Task {uid} cancelled")
            finally:
                result = None

        return result

    async def _schedule(self, uid, call, sched):
        """Executes a call uid to the command cmd following the
        scheduling (time) properties of sched
        
        Arguments:
            uid {string} -- The call unique id
            cmd {string} -- The command to be called/executed
            sched {dict} -- Contains keys that determine the timely manner
            that the cmd is going to be called
        
        Returns:
            list -- A list of results of the called cmd according to sched parameters
        """
        logger.debug(f"Scheduling call uid {uid}")
        logger.debug(f"Schedule parameters: {sched}")
        loop = asyncio.get_event_loop()
        results = []

        begin = sched.get("from", 0)
        finish = sched.get("until", 0)
        duration = sched.get("duration", 0)
        repeat = sched.get("repeat", 0)
        interval = sched.get("interval", 0)

        timeout = 0
        task_duration = 0
        repeat = 1 if repeat == 0 else repeat

        for _ in range(repeat):

            await asyncio.sleep(begin)
            begin = interval

            task = loop.create_task(call)
            logger.debug(f"Task {uid} created {task}")
            
            task_duration = await self._check_task(uid, task, duration)
            result = await self._check_task_result(uid, task)

            if result:
                logger.debug(f"Task {uid} result available")
                results.append(result)
            else:
                logger.debug(f"Task {uid} result unavailable")
           
            timeout += task_duration + interval
            if self._check_finish(uid, finish, timeout):            
                break
            
        return results

    async def _build(self, calls):
        """Builds list of command calls as coroutines to be
        executed by asyncio loop
        
        Arguments:
            calls {list} -- List of command calls
        
        Returns:
            list -- Set of coroutines scheduled to be called
        """
        logger.debug(f"Building calls into coroutines")
        aws = []
        for uid, (call, call_sched) in calls.items():
            aw = self._schedule(uid, call, call_sched)
            aws.append(aw)

        return aws

    async def run(self, calls):
        """Executes the list of calls as coroutines
        returning their results
        
        Arguments:
            calls {list} -- Set of commands to be scheduled and called as subprocesses
        
        Returns:
            dict -- Results of calls (stdout/stderr) indexed by call uid
        """
        results = {}

        aws = await self._build(calls)

        logger.debug(f"Running built coroutines")
        tasks = await asyncio.gather(*aws, return_exceptions=True)

        calls_ids = list(calls.keys())
        counter = 0

        for aw in tasks:
            uid = calls_ids[counter]

            if isinstance(aw, Exception):
                logger.debug(f"Could not run _schedule {calls[uid]} - exception {aw}")
            else:
                if aw:
                    results[uid] = aw.pop()
                else:
                    results[uid] = {}

            counter += 1

        return results
