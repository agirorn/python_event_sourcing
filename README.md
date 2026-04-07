# Python event sourcing

## setup

```shell
uv sync
```

## system setup

__Install [uv]__

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

__Install pnpm__

```shell
brew install pnpm
```

__Install mprocs__

```shell
brew install mprocs
```

__Install pgmt

Assuming `~/bin` is in your PATH enviroment variable else you should copy pgmt
to a folcder in your PATH

```shell
git clone git@github.com:agirorn/pgmt.git \
    && cd pgmt \
    && cargo build \
    && cp ./target/debug/pgmt ~/bin
```

__Update [uv]__
```shell
make setup
```

## Start

```shell
make start
```

## Database migration

```shell
make db-migrate
```


[uv](https://github.com/astral-sh/uv)
