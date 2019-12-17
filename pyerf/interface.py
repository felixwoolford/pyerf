import os
from IPython import terminal
import asyncio
from prompt_toolkit.patch_stdout import patch_stdout

# def enable_gui(self, gui=None):
    # if gui and (gui != 'inline') :
        # self.active_eventloop, self._inputhook = get_inputhook_name_and_func(gui)
    # else:
        # self.active_eventloop = self._inputhook = None

    # if PTK3:
        # if self._inputhook:
            # from prompt_toolkit.eventloop import set_eventloop_with_inputhook
            # set_eventloop_with_inputhook(self._inputhook)
        # else:
            # import asyncio
            # asyncio.set_event_loop(asyncio.new_event_loop())

# patch for TerminalInteractiveShell to allow stdout to show through
# one day this may need correcting but it's good for now
# Maybe I could also inject something to fix that SQLite shit
def prompt_for_code(self):
    if self.rl_next_input:
        default = self.rl_next_input
        self.rl_next_input = None
    else:
        default = ''

    with patch_stdout(raw=True):
        text = self.pt_app.prompt( default=default, **self._extra_prompt_options())
    return text

class CLI:
    def __init__(self, core):
        self.core = core
    
    # set var in between experiment iterations, should make behaviour more predictable
    def safe_set(self, target, var, val):
        with self.core._iteration_lock:
            vars(target)[var] = val
    
    # call function in between experiment iterations, should make behaviour more predictable
    def safe(self, func):
        with self.core._iteration_lock:
            func()

    def _run(self):
        i = self
        c = self.core
        if c._mode == "visual":
            g = self.core.gui
        e = self.core.experiment

        # inject my hacked solution to prevent a new eventloop being created in terminal
        terminal.interactiveshell.TerminalInteractiveShell.prompt_for_code = prompt_for_code
        # terminal.interactiveshell.TerminalInteractiveShell.enable_gui = enable_gui
        # asyncio.set_event_loop(self.loop)
        asyncio.set_event_loop(asyncio.new_event_loop())
        terminal.embed.embed()

    def q(self):
        if self.core._mode == "visual":
            self.core.gui.quit()
        self.core._kill = True
        self.core.reset()
        os._exit(1)
