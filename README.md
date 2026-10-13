# Nicholas Beroud · personal portfolio

First draft of a personal website about markets, policy and technology.

## Preview

Run `python3 -m http.server 4173 --bind 127.0.0.1` from this directory, then visit http://127.0.0.1:4173.

Plain HTML and CSS, with no build step or external runtime dependencies. `index.html` contains the introduction and listings; `projects/` and `notes/` contain individual pages; `assets/style.css` controls the shared appearance.

## Draft state

- The résumé icon opens the supplied October 2026 PDF in a new tab. The original PDF is stored unchanged at `assets/nicholas-beroud-resume.pdf`; the link has no download attribute.
- Notes now include a short team hackathon recap based on the supplied event post and a sourced thesis explainer. The two older outline files remain unlisted.
- The thesis uses its full title, an existing research figure (9 October 2026 vintage), and an institutional hypothesis with limitations. Its private research repository is not linked.
- The repo-model page credits Eleonora Björnberg and links to her original public project.
- All pages have `noindex, nofollow` until a deliberate launch.
- GitHub automatically enabled Pages after the repository rename. It is now configured for Actions/workflow publishing, with no deployment workflow in this draft. Pushing this branch does not deploy the portfolio.

Before launch: finalize the About; review the new note copy; add reviewed thesis material; confirm the club-site URL if linking it; remove noindex only when ready. Then explicitly configure deployment from the approved branch.
