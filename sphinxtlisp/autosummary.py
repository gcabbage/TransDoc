# -*- coding: utf-8 -*-

import re

from sphinx.ext.autosummary import Autosummary

class TLispSummary(Autosummary):
    
    def get_items(self, names):
        # type: (List[unicode]) -> List[Tuple[unicode, unicode, unicode, unicode]]
        """Try to import the given names, and return a list of
        ``[(name, signature, summary_string, real_name), ...]``.
        """
        env = self.state.document.settings.env

        items = []  # type: List[Tuple[unicode, unicode, unicode, unicode]]

        max_item_chars = 50

        tlispfuncs = self.env.config._tlispfuncs
        fncnames = []
        # Autoexpand any names if required
        for name in names:
            if name.endswith('*'):
                fncnames.extend([n for n in tlispfuncs if n.startswith(name[:-1].lower())])
            else:
                fncnames.append(name)
        for name in fncnames:
            obj =  tlispfuncs[name.lower()]
            doc = list(obj.lines())
            while doc and not doc[0].strip():
                doc.pop(0)

            for i, piece in enumerate(doc):
                if not piece.strip():
                    doc = doc[:i]
                    break
            # Try to find the "first sentence", which may span multiple lines
            m = re.search(r"^([A-Z].*?\.)(?:\s|$)", " ".join(doc).strip())
            if m:
                summary = m.group(1).strip()
            elif doc:
                summary = doc[0].strip()
            else:
                summary = ''

            items.append((obj.tlisp_signature, '', summary, name))
        
        return items
