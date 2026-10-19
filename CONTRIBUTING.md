# Contributing to Knode

Thanks for helping. Knode is built in public, and contributions of every size are welcome:
code, docs, design, bug reports and ideas.

## Before you start

1. Read the [handbook](https://github.com/knodemd/handbook), especially *How we work*.
2. **Every change starts with an issue.** Look for an existing one, or open one and describe
   the problem before the solution. Issues labelled `good first issue` are a good place to begin.
3. Comment on the issue to say you're taking it, so nobody duplicates the work.

## Making a change

1. Fork the repository and create a branch named `<type>/<short-description>`, for example
   `feat/import-markdown` or `fix/crash-on-empty-map`.
2. Keep commits small and use [Conventional Commits](https://www.conventionalcommits.org):
   `type(scope): subject`, in English and the imperative (`feat(import): parse Claude exports`).
3. Run the tests and linters the repository describes in its README.
4. Open a pull request that says **why** the change is needed, **what** changed and **how you
   tested it**, and links the issue (`Closes #12` or `Part of #12`).

## Reviews

A maintainer reviews every pull request. Expect questions: they're about the change, not about you.
Pull requests are squash-merged once approved and the checks pass.

## Brand and design

Use the assets in [knodemd/brand](https://github.com/knodemd/brand) and follow its guidelines.
Please don't add new colours, typefaces or icon styles; propose them in an issue first.

## Licence

Knode's repositories are licensed under [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0):
by contributing, you agree that your contribution is licensed under it too. The Knode name, logo,
icons and typefaces are reserved under the [Knode Brand License](https://github.com/knodemd/brand-license).
See [decision 0003](https://github.com/knodemd/handbook/blob/main/decisions/0003-licences.md).
