
        text = _norm(raw)
        if not text:
            continue

        # Expand coordinated symptom phrases so "pain in X and Y" can
        # contribute both normalized terms without inventing new labels.
        candidates = [text]
        if " and " in text:
            parts = [part.strip() for part in text.split(" and ") if part.strip()]
            candidates.extend(parts)
            prefix = parts[0].split()[:2] if parts and len(parts[0].split()) >= 3 else []
            if prefix and " ".join(prefix) in {"pain in", "feeling of"}:
                candidates.extend(
                    f"{' '.join(prefix)} {part}" for part in parts[1:]
                )

        matched = False
        matched_keys = set()
        for term in VOCABULARY:
            aliases = (_norm(term.key), _norm(term.display_name), *map(_norm, term.aliases))
            if any(
                alias and any(alias in candidate or candidate in alias for candidate in candidates)
                for alias in aliases
            ):
                if term.key not in found:
                    found.append(term.key)
                if term.key not in matched_keys:
                    evidence.setdefault(term.key, []).append(raw)
                    matched_keys.add(term.key)
                matched = True

        if not matched:
            unmapped.append(raw)

    domains = sorted({term.domain for term in VOCABULARY if term.key in found})
    return {
        "feature_schema": "menstrual_context_v1",
        "terms_found": found,