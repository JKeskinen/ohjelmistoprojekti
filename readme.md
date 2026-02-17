
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

#### Esimerkki: Päivitä fork alkuperäisestä reposta (upstream)

1. Hae muutokset alkuperäisestä reposta:
	```sh
	git fetch upstream
	```
2. Siirrä (rebase) muutokset omaan branchiin:
	```sh
	git rebase upstream/main
	```
3. Jos haluat viedä muutokset omaan GitHub-forkkiin:
	```sh
	git push origin main
	```

#### Jos tulee rabsen kanssa ongelmia

1. Korjaa "Ghost-rebase" ongelma:
	```sh
	git rebase --abort
	```
2. Jos ei toimi, niin suorita tämän:
	```sh
	rm -r -fo .git\rebase-merge
	```
3. Yritä uudestaan:
	```sh
	git status
	```
4. Jos: 
	```sh
	On branch main
	Your branch is up to date with 'origin/main'.
	
	nothing to commit, working tree clean
	```
5. Niin pitäisi onnistua:
	```sh
	git rebase upstream/main
	```