from typing import TypedDict, Optional


class ClientCapabilities (TypedDict):
    pass


class InitializeParams(TypedDict):
    # https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#initializeParams
    rootUri: str
    capabilities: ClientCapabilities


class Request(TypedDict):
    # "2.0"
    jsonrpc: str
    # increment
    id: int
    # "textDocument/didOpen"
    method: str
    params: dict
