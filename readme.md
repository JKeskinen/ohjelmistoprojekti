
## Forkatun repon päivittäminen alkuperäisestä (upstream) ja omasta (origin) reposta

### 1. Lisää alkuperäinen repo (upstream), jos sitä ei ole jo lisätty:
```sh
git remote add upstream https://github.com/JKeskinen/ohjelmistoprojekti
```

### 2. Tarkista remotes:
```sh
git remote -v
```

### 3. Päivitä oma fork (origin) ja tarkista tila:
```sh
git fetch origin
git status
```

### 4. Päivitä alkuperäisestä reposta (upstream):
```sh
git fetch upstream
```

### 5. Yhdistä upstreamin muutokset omaan branchiin:
```sh
git rebase upstream/main
```

### 6. Jos haluat päivittää GitHubiin:
```sh
git push origin main
```

---

Komennolla `git pull --rebase` saa päivitettyä repon ajantasalle, mutta forkatuissa projekteissa upstreamin muutokset pitää hakea erikseen yllä olevilla komennoilla.