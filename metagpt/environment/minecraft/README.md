# Minecraft Environment

## Code execution boundary

The Mineflayer runner executes the generated `programs` and `code` with `eval()`
inside the Mineflayer Node.js process. This code has the same filesystem,
network, environment-variable, and process privileges as that process; it is
not executed in a separate sandbox.

Run the Minecraft environment only in an isolated, disposable environment,
and do not expose its execution endpoint to untrusted callers. Review or
constrain generated code before execution when the model input or skill source
is not fully trusted. See the execution path in
[`mineflayer/index.js`](mineflayer/index.js).
