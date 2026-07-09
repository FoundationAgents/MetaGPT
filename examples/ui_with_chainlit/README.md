# MetaGPT in UI with Chainlit! 🤖

- MetaGPT functionality in UI using Chainlit.
- It also takes a **one line requirement** as input and outputs **user stories / competitive analysis / requirements / data structures / APIs / documents, etc.**, But `everything in UI`.

## Install Chainlit

- Setup initial MetaGPT config from [Main](../../README.md).

```bash
pip install chainlit
```

## Usage

```bash
chainlit run app.py
```

- Now go to: http://localhost:8000

- Default login: `admin` / `admin` (configurable via `CHAINLIT_USERNAME` and `CHAINLIT_PASSWORD` environment variables).

- Select,
  - `Create a 2048 game`
  - `Write a cli Blackjack Game`
  - `Type your own message...`

- It will run a metagpt software company.

## To Setup with own application

- We can change `Environment.run`, `Team.run`, `Role.run`, `Role._act`, `Action.run`.
- In this code, changed `Environment.run`, as it was easier to do.
- We will need to change `metagpt.logs.set_llm_stream_logfunc` to stream messages in UI with Chainlit Message.
- To use at some other place we need to call `chainlit.Message(content="").send()` with content.