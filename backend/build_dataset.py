"""Parse Allegato 1 raw text into a clean allergens.json dataset."""
import json
from pathlib import Path

RAW = """f1 Albume Alimenti 0090681.01 IGE SPEC.ALLERG.QUANT. (<5) - f1 - Albume
f10 Semi di sesamo (Sesamum indicum) Alimenti 0090681.10 IGE SPEC.ALLERG.QUANT. (<5) - f10 - Semi di sesamo
f11 Grano saraceno (Fagopyrum esculentum) Alimenti 0090681.11 IGE SPEC.ALLERG.QUANT. (<5) - f11 - Grano saraceno
f12 Piselli (Pisum sativum) Alimenti 0090681.12 IGE SPEC.ALLERG.QUANT. (<5) - f12 - Piselli
f124 Farro (Triticum spelta) Alimenti 0090681.51 IGE SPEC.ALLERG.QUANT. (<5) - f124 - Farro
f13 Arachide (Arachis hypogaea) Alimenti 0090681.13 IGE SPEC.ALLERG.QUANT. (<5) - f13 - Arachide
f14 Semi di soia (Glycine max) Alimenti 0090681.14 IGE SPEC.ALLERG.QUANT. (<5) - f14 - Semi di soia
f15 Fagioli bianchi (Phaseolus vulgaris) Alimenti 0090681.15 IGE SPEC.ALLERG.QUANT. (<5) - f15 - Fagiolo bianco
f17 Nocciola (Corylus avellana) Alimenti 0090681.16 IGE SPEC.ALLERG.QUANT. (<5) - f17 - Nocciola
f18 Noce brasiliana (Bertholletia excelsa) Alimenti 0090681.17 IGE SPEC.ALLERG.QUANT. (<5) - f18 - Noce brasiliana
f2 Latte Alimenti 0090681.02 IGE SPEC.ALLERG.QUANT. (<5) - f2 - Latte
f20 Mandorla (Amygdalus communis) Alimenti 0090681.18 IGE SPEC.ALLERG.QUANT. (<5) - f20 -Mandorla
f202 Anacardio (Anacardium occidentale) Alimenti 0090681.53 IGE SPEC.ALLERG.QUANT. (<5) - f202 - Anacardio
f203 Pistacchio (Pistacia vera) Alimenti 0090681.54 IGE SPEC.ALLERG.QUANT. (<5) - f203 - Pistacchio
f207 Vongola (Ruditapes spp.) Alimenti 0090681.57 IGE SPEC.ALLERG.QUANT. (<5) - f207 - Vongola
f208 Limone (Citrus limon) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f210 Ananas (Ananas comosus) Alimenti 0090681.58 IGE SPEC.ALLERG.QUANT. (<5) - f210 Ananas
f211 Mora (Rubus fruticosus) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f213 Carne di coniglio (Oryctolagus spp.) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f214 Spinaci (Spinachia oleracea) Alimenti 0090681.60 IGE SPEC.ALLERG.QUANT. (<5) - f214 - Spinaci
f215 Lattuga (Lactuca sativa) Alimenti 0090681.61 IGE SPEC.ALLERG.QUANT. (<5) - f215 - Lattuga
f216 Cavolo (Brassica oleracea var. italica) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f218 Paprica, Peperone (Capsicum annuum) Alimenti 0090681.62 IGE SPEC.ALLERG.QUANT. (<5) - f218 - Paprika (peperone)
f224 Semi di papavero (Papaver somniferum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f225 Zucca (Cucurbita pepo) Alimenti 0090681.64 IGE SPEC.ALLERG.QUANT. (<5) - f225 - Zucca
f226 Semi di zucca (Curcubita pepo) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f23 Granchio comune (Cancer pagurus) Alimenti 0090681.19 IGE SPEC.ALLERG.QUANT. (<5) - f23 - Granchio comune
f231 Latte bollito Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f234 Vaniglia (Vanilla planifolia) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f235 Lenticchia (Lens esculenta) Alimenti 0090681.65 IGE SPEC.ALLERG.QUANT. (<5) - f235 - Lenticchie
f237 Albicocca (Prunus armeniaca) Alimenti 0090681.66 IGE SPEC.ALLERG.QUANT. (<5) - f237 - Albicocca
f24 Gambero (Pandalus borealis, Penaeus monodon) Alimenti 0090681.20 IGE SPEC.ALLERG.QUANT. (<5) - f24 - Gambero
f242 Ciliegia (Prunus avium) Alimenti 0090681.67 IGE SPEC.ALLERG.QUANT. (<5) - f242 - Ciliegia
f244 Cetriolo (Cucumis sativus) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f246 Gomma di guar (E412) (Cyamopsis tetragonolobus) Alimenti 0090681.68 IGE SPEC.ALLERG.QUANT. (<5) - f246 - Gomma di Guar
f25 Pomodoro (Lycopersicon lycopersicum) Alimenti 0090681.21 IGE SPEC.ALLERG.QUANT. (<5) - f25 - Pomodoro
f253 Pinoli (Pinus edulis) Alimenti 0090681.69 IGE SPEC.ALLERG.QUANT. (<5) - f253 - Pinoli
f254 Platessa (Pleuronectes platessa) Alimenti 0090681.70 IGE SPEC.ALLERG.QUANT. (<5) - f254 - Platessa
f255 Prugna (Prunus domestica) Alimenti 0090681.71 IGE SPEC.ALLERG.QUANT. (<5) - f255 - Prugna
f256 Noce (Juglans spp.) Alimenti 0090681.72 IGE SPEC.ALLERG.QUANT. (<5) - f256 - Noce
f259 Uva (Vitis vinifera) Alimenti 0090681.74 IGE SPEC.ALLERG.QUANT. (<5) - f259 - Uva
f26 Carne di maiale (Sus spp. ) Alimenti 0090681.22 IGE SPEC.ALLERG.QUANT. (<5) - f26 - Maiale
f261 Asparago (Asparagus officinalis) Alimenti 0090681.76 IGE SPEC.ALLERG.QUANT. (<5) - f261 - Asparago
f27 Carne di bue (Bos spp. ) Alimenti 0090681.23 IGE SPEC.ALLERG.QUANT. (<5) - f27 - Bue/Manzo
f270 Zenzero (Zingiber officinale) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f279 Pepe di cayenna (Capisicum frutescens) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f280 Pepe nero (Piper nigrum) Alimenti 0090681.80 IGE SPEC.ALLERG.QUANT. (<5) - f280 - Pepe nero
f284 Carne di tacchino (Meleagris gallopavo) Alimenti 0090681.81 IGE SPEC.ALLERG.QUANT. (<5) - f284 - Tacchino
f288 Mirtillo nero (Vaccinium myrtillis) Alimenti 0090681.83 IGE SPEC.ALLERG.QUANT. (<5) - f288 - Mirtillo nero
f293 Papaya (Carica papaya) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f294 Frutto della passione (Passiflora edulis) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f296 Carruba (E410) (Ceratonia siliqua) Alimenti 0090681.85 IGE SPEC.ALLERG.QUANT. (<5) - f296 - Carruba
f297 Gomma arabica (E414) (Acacia spp.) Alimenti 0090681.86 IGE SPEC.ALLERG.QUANT. (<5) - f297 - Gomma arabica
f299 Castagna (Castanea sativa) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f3 Pesce, Merluzzo (Gadus morhua) Alimenti 0090681.03 IGE SPEC.ALLERG.QUANT. (<5) - f3 - Pesce (merluzzo)
f300 Latte di capra Alimenti 0090681.87 IGE SPEC.ALLERG.QUANT. (<5) - f300 - Latte di capra
f301 Kaki (Diospyros kaki) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f31 Carota (Daucus carota) Alimenti 0090681.24 IGE SPEC.ALLERG.QUANT. (<5) - f31 - Carota
f316 Semi di colza (Brassica napus) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f317 Coriandolo (Coriandrum sativum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f33 Arancia (Citrus sinensis) Alimenti 0090681.25 IGE SPEC.ALLERG.QUANT. (<5) - f33 - Arancia
f332 Menta (Mentha piperita) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f333 Semi di lino (Linum usitatissimum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f335 Semi di lupino (Lupinus albus) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f343 Lampone (Rubus idaeus) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f345 Noce di macadamia (Macadamia spp.) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f347 Quinoa (Chenopodium quinoa) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f35 Patata (Solanum tuberosum) Alimenti 0090681.26 IGE SPEC.ALLERG.QUANT. (<5) - f35 - Patata
f36 Noce di cocco (Cocus nucifera) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f37 Mitile (Mytilus edulis) Alimenti 0090681.30 IGE SPEC.ALLERG.QUANT. (<5) - f44 - Mitili
f4 Grano (Triticum aestivum) Alimenti 0090681.04 IGE SPEC.ALLERG.QUANT. (<5) - f4 - Grano (frumento)
f40 Tonno (Thunnus albacares) Alimenti 0090681.27 IGE SPEC.ALLERG.QUANT. (<5) - f40 - Tonno
f41 Salmone (Salmo salar) Alimenti 0090681.28 IGE SPEC.ALLERG.QUANT. (<5) - f41 - Salmone
f44 Fragola (Fragaria vesca) Alimenti 0090681.29 IGE SPEC.ALLERG.QUANT. (<5) - f44 - Fragola
f45 Lievito (Saccharomyces cerevisiae) Alimenti 0090681.31 IGE SPEC.ALLERG.QUANT. (<5) - f45 - Lievito
f47 Aglio (Allium sativum) Alimenti 0090681.32 IGE SPEC.ALLERG.QUANT. (<5) - f47 - Aglio
f48 Cipolla (Allium cepa) Alimenti 0090681.33 IGE SPEC.ALLERG.QUANT. (<5) - f48 - Cipolla
f49 Mela (Malus x domestica) Alimenti 0090681.34 IGE SPEC.ALLERG.QUANT. (<5) - f49 - Mela
f5 Segale (Secale cereale) Alimenti 0090681.05 IGE SPEC.ALLERG.QUANT. (<5) - f5 - Segale (farina)
f51 Germogli di bambu (Phyllostachys pubescens) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f55 Miglio comune (Panicum milliaceum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f58 Seppia (Todarodes pacificus) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f59 Polpo (Octopus vulgaris) Alimenti 0090681.35 IGE SPEC.ALLERG.QUANT. (<5) - f59 - Polpo
f6 Orzo (Hordeum volgare) Alimenti 0090681.06 IGE SPEC.ALLERG.QUANT. (<5) - f6 - Orzo
f7 Avena (Avena sativa) Alimenti 0090681.07 IGE SPEC.ALLERG.QUANT. (<5) - f7 - Avena (farina)
f75 Tuorlo Alimenti 0090681.36 IGE SPEC.ALLERG.QUANT. (<5) - f75 - Tuorlo d'uovo
f79 Glutine Alimenti 0090681.37 IGE SPEC.ALLERG.QUANT. (<5) - f79 - Glutine
f8 Granoturco (Zea mays) Alimenti 0090681.08 IGE SPEC.ALLERG.QUANT. (<5) - f8 - Mais
f80 Astice (Homarus Gammarus) Alimenti 0090681.38 IGE SPEC.ALLERG.QUANT. (<5) - f80 - Astice
f83 Carne di pollo (Gallus spp.) Alimenti 0090681.39 IGE SPEC.ALLERG.QUANT. (<5) - f83 - Pollo
f84 Kiwi (Actinidia deliciosa) Alimenti 0090681.40 IGE SPEC.ALLERG.QUANT. (<5) - f84 - Kiwi
f85 Sedano (Apium graveolens) Alimenti 0090681.41 IGE SPEC.ALLERG.QUANT. (<5) - f85 - Sedano
f86 Prezzemolo (Petroselinum crispum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f87 Melone (Cucumis melo spp.) Alimenti 0090681.42 IGE SPEC.ALLERG.QUANT. (<5) - f87 - Melone
f88 Carne di montone (Ovis spp.) Alimenti 0090681.43 IGE SPEC.ALLERG.QUANT. (<5) - f88 - Montone
f89 Senape (Brassica/Sinapis spp.) Alimenti 0090681.44 IGE SPEC.ALLERG.QUANT. (<5) - f89 - Senape
f9 Riso integrale (Oryza sativa) Alimenti 0090681.09 IGE SPEC.ALLERG.QUANT. (<5) - f9 - Riso
f90 Malto Alimenti 0090681.45 IGE SPEC.ALLERG.QUANT. (<5) - f90 - Malto
f91 Mango (Mangifera indica) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
f92 Banana (Musa spp.) Alimenti 0090681.46 IGE SPEC.ALLERG.QUANT. (<5) - f92 - Banana
f94 Pera (Pyrus communis) Alimenti 0090681.48 IGE SPEC.ALLERG.QUANT. (<5) - f94 - Pera
f95 Pesca (Prunus persica) Alimenti 0090681.49 IGE SPEC.ALLERG.QUANT. (<5) - f95 - Pesca
f96 Avocado (Persea americana) Alimenti 0090681.50 IGE SPEC.ALLERG.QUANT. (<5) - f96 - Avocado
p1 Ascaris Alimenti 0090681.E0 IGE SPEC.ALLERG.QUANT. (<5) - p1 - Ascaris
p4 Anisakis Alimenti 0090681.E1 IGE SPEC.ALLERG.QUANT. (<5) - p4 - Anisakis
Rf206 Sgombro (Scomber scombrus) Alimenti 0090681.56 IGE SPEC.ALLERG.QUANT. (<5) - f206 - Sgombro
Rf212 Funghi, champignon (Agaricus hortensis) Alimenti 0090681.59 IGE SPEC.ALLERG.QUANT. (<5) - f212 - Funghi (champignon)
Rf258 Calamaro (Loligo spp.) Alimenti 0090681.73 IGE SPEC.ALLERG.QUANT. (<5) - f258 - Calamaro
Rf262 Melanzana (Solanum melongena) Alimenti 0090681.77 IGE SPEC.ALLERG.QUANT. (<5) - f262 - Melanzana
Rf265 Cumino (Carum carvi) Alimenti 0090681.78 IGE SPEC.ALLERG.QUANT. (<5) - f265 - Cumino
Rf266 Macis (Myristica fragrans) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf267 Cardamomo (Elettaria cardamomum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf268 Chiodi di garofano (Syzygiun aromaticum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf269 Basilico (Ocimum basilicum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf271 Anice (Pimpinella anisum) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf276 Finocchio fresco (Foeniculum vulgare) Alimenti 0090681.79 IGE SPEC.ALLERG.QUANT. (<5) - f276 - Finocchio
Rf302 Mandarino (Citrus reticulata) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf304 Aragosta (Palinurus spp) Alimenti 0090681.88 IGE SPEC.ALLERG.QUANT. (<5) - f304 - Aragosta
Rf308 Sardina europea (Sardina pilchardus) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf309 Ceci (Cicer arietinus) Alimenti 0090681.89 IGE SPEC.ALLERG.QUANT. (<5) - f309 - Ceci
Rf312 Pesce Spada (Xiphias gladius) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf314 Lumaca (Helix aspersa) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf319 Barbabietola rossa (Beta vulgaris) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf328 Fico (Ficus carica) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rf329 Anguria (Citrullus lanatus) Alimenti 0090681.90 IGE SPEC.ALLERG.QUANT. (<5) - f329 - Anguria
Rf342 Oliva (Olea europaea) Alimenti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
d202 Der p 1, Acaro della polvere domestica (Dermatophagoides Pteronyssinus) Allergeni molecolari 009068A.13 IGE SPEC.RICOMB.MOL. - nDer p 1
d203 Der p 2, Acaro della polvere domestica (Dermatophagoides Pteronyssinus) Allergeni molecolari 009068A.57 IGE SPEC.RICOMB.MOL. - rDer p 2
d205 Der p 10, Acaro della polvere domestica, Tropomiosina (Dermatophagoides Pteronyssinus) Allergeni molecolari 009068A.56 IGE SPEC.RICOMB.MOL. - rDer p 10
d209 Der p 23, Acaro della polvere domestica (Dermatophagoides Pteronyssinus) Allergeni molecolari 009068A.99 IGE SPEC.RICOMB.MOL. -rDer p 23
e101 Can f 1, Cane (Canis familiaris) Allergeni molecolari 009068A.46 IGE SPEC.RICOMB.MOL. - rCan f 1
e102 Can f 2, Cane (Canis familiaris) Allergeni molecolari 009068A.47 IGE SPEC.RICOMB.MOL. - rCan f 2
e220 Fel d 2, Gatto, Albumina sierica (Felis domesticus) Allergeni molecolari 009068A.60 IGE SPEC.RICOMB.MOL. - rFel d 2
e226 Can f 5, Cane (Canis familiaris) Allergeni molecolari 009068A.49 IGE SPEC.RICOMB.MOL. - rCan f 5
e228 Fel d 4, Gatto (Felis domesticus) Allergeni molecolari 009068A.61 IGE SPEC.RICOMB.MOL. - rFel d 4
e94 Fel d 1, Gatto (Felis domesticus) Allergeni molecolari 009068A.59 IGE SPEC.RICOMB.MOL. - rFel d 1
f232 Gal d 2, Uovo, Ovoalbumina (Gallus domesticus) Allergeni molecolari 009068A.15 IGE SPEC.RICOMB.MOL. - nGal d 2
f233 Gal d 1, Uovo, Ovomucoide (Gallus domesticus) Allergeni molecolari 009068A.14 IGE SPEC.RICOMB.MOL. - nGal d 1
f351 Pen a 1, Gamberetto, Tropomiosina (Penaeus aztecus) Allergeni molecolari 009068A.78 IGE SPEC.RICOMB.MOL. - rPen a 1
f353 Gly m 4, Soia, PR-10 (Glycine max) Allergeni molecolari 009068A.64 IGE SPEC.RICOMB.MOL. - rGly m 4 (PR-10)
f354 Ber e 1, Noce brasiliana (Bertholletia excelsa) Allergeni molecolari 009068A.41 IGE SPEC.RICOMB.MOL. - rBer e 1
f416 Tri a 19, Grano, Omega-5 Gliadina (Triticum aestivum) Allergeni molecolari 009068A.94 IGE SPEC.RICOMB.MOL. - rTri a 19
f420 Pru p 3, Pesca, LTP (Prunus persica) Allergeni molecolari 009068A.89 IGE SPEC.RICOMB.MOL. - rPru p 3 (LPT)
f422 Ara h 1, Arachide (Arachis hypogaea) Allergeni molecolari 009068A.31 IGE SPEC.RICOMB.MOL. - rAra h 1
f423 Ara h 2, Arachide (Arachis hypogaea) Allergeni molecolari 009068A.32 IGE SPEC.RICOMB.MOL. - rAra h 2
f424 Ara h 3, Arachide (Arachis hypogaea) Allergeni molecolari 009068A.33 IGE SPEC.RICOMB.MOL. - rAra h 3
f425 Cor a 8, Nocciola, LTP (Corylus avellana) Allergeni molecolari 009068A.53 IGE SPEC.RICOMB.MOL. - rCor a 8
f426 Gad c 1, Merluzzo, Parvalbumina (Gadus morhua) Allergeni molecolari 009068A.63 IGE SPEC.RICOMB.MOL. - rGad c 1
f427 Ara h 9, Arachide, LTP (Arachis hypogaea) Allergeni molecolari 009068A.98 IGE SPEC.RICOMB.MOL. -rAra h 9 (LTP)
f431 Gly m 5, Soia, Beta-conglicinina (Glycine max) Allergeni molecolari 009068A.18 IGE SPEC.RICOMB.MOL. - nGly m 5
f432 Gly m 6, Soia, Glicinina (Glycine max) Allergeni molecolari 009068A.19 IGE SPEC.RICOMB.MOL. - nGly m 6
f433 Tri a 14, Grano, LTP (Triticum aestivum) Allergeni molecolari 009068A.93 IGE SPEC.RICOMB.MOL. - rTri a 14 (LTP)
f435 Mal d 3, Mela, LTP (Malus domestica) Allergeni molecolari 009068A.74 IGE SPEC.RICOMB.MOL. - rMal d 3 (LTP)
f439 Cor a 14, Nocciola (Corylus avellana) Allergeni molecolari 009068A.52 IGE SPEC.RICOMB.MOL. - rCor a 14
f440 Cor a 9, Nocciola (Corylus avellana) Allergeni molecolari 009068A.54 IGE SPEC.RICOMB.MOL. - rCor a 9
f441 Jug r 1, Noce (Juglans regia) Allergeni molecolari 009068A.71 IGE SPEC.RICOMB.MOL. - rJug r 1
f442 Jug r 3, Noce, LTP (Juglans regia) Allergeni molecolari 009068A.72 IGE SPEC.RICOMB.MOL. - rJug r 3 (LTP)
f443 Ana o 3, Anacardo (Anacardium occidentale) Allergeni molecolari 009068A.24 IGE SPEC.RICOMB.MOL. - rAna o 3
f449 Ses i 1, 2S Albumina, Sesamo (Sesamum Indicum) Allergeni molecolari 009068A.92 IGE SPEC.RICOMB.MOL. - rSes i 1
f454 Pru p 7, Pesca, GRP (Prunus persica) Allergeni molecolari 009068A.91 IGE SPEC.RICOMB.MOL. - rPru p 7
f76 Bos d 4, Latte, Alfa-lattoalbumina (Bos domesticus) Allergeni molecolari 009068A.06 IGE SPEC.RICOMB.MOL. - nBos d 4 (Alfa-lattoalbumina)
f77 Bos d 5, Latte, Beta-lattoglobulina (Bos domesticus) Allergeni molecolari 009068A.07 IGE SPEC.RICOMB.MOL. - nBos d 5 (Beta-lattoglobulina)
f78 Bos d 8, Latte, Caseina (Bos domesticus) Allergeni molecolari 009068A.09 IGE SPEC.RICOMB.MOL. - nBos d 8 (Caseina)
f98 Gliadina (Triticum aestivum) Allergeni molecolari 0090681.H0 IGE SPEC.ALLERG.QUANT. (<5) - Gliadina
g205 Phl p 1, Coda di topo (Phleum pratense) Allergeni molecolari 009068A.79 IGE SPEC.RICOMB.MOL. - rPhl p 1
g210 Phl p 7, Coda di topo (Phleum pratense - Polcalcina) Allergeni molecolari 009068A.A0 IGE SPEC.RICOMB.MOL. - rPhl p 7
g215 Phl p 5b, Coda di topo (Phleum pratense) Allergeni molecolari 009068A.83 IGE SPEC.RICOMB.MOL. - rPhl p 5b
i208 Api m 1, Ape, Fosfolipasi A2 (Apis mellifera) Allergeni molecolari 009068A.26 IGE SPEC.RICOMB.MOL. - rApi m 1
i209 Ves v 5, Vespa, Vitellogenina (Vespula vulgaris) Allergeni molecolari 009068A.96 IGE SPEC.RICOMB.MOL. - rVes v 5
i210 Pol d 5, Vespa cartonaia, Antigene 5 (Polistes dominulus) Allergeni molecolari 009068A.87 IGE SPEC.RICOMB.MOL. - rPol d 5
i211 Ves v 1, Vespa, Fosfolipasi A1 (Vespula vulgaris) Allergeni molecolari 009068A.95 IGE SPEC.RICOMB.MOL. - rVes v 1
i214 Api m 2, Ape, Ialuronidasi (Apis mellifera) Allergeni molecolari 009068A.29 IGE SPEC.RICOMB.MOL. - rApi m 2
i215 Api m 3, Ape, Fosfatasi acida (Apis mellifera) Allergeni molecolari 009068A.28 IGE SPEC.RICOMB.MOL. - rApi m 3
i216 Api m 5, Ape, Dipeptil-peptidasi IV (Apis mellifera) Allergeni molecolari 009068A.30 IGE SPEC.RICOMB.MOL. - rApi m 5
i217 Api m 10, Ape, Icarapina variante 2 (Apis mellifera) Allergeni molecolari 009068A.27 IGE SPEC.RICOMB.MOL. - rApi m 10
k208 Gal d 4, Uovo, Lisozima (Gallus domesticus) Allergeni molecolari 009068A.17 IGE SPEC.RICOMB.MOL. - nGal d 4
k215 Hev b 1, Lattice (Hevea brasiliensis) Allergeni molecolari 009068A.65 IGE SPEC.RICOMB.MOL. - rHev b 1
k217 Hev b 3, Lattice (Hevea brasiliensis) Allergeni molecolari 009068A.67 IGE SPEC.RICOMB.MOL. - rHev b 3
k218 Hev b 5, Lattice (Hevea brasiliensis) Allergeni molecolari 009068A.68 IGE SPEC.RICOMB.MOL. - rHev b 5
k220 Hev b 6.02, Lattice (Hevea brasiliensis) Allergeni molecolari 009068A.69 IGE SPEC.RICOMB.MOL. - rHev b 6.02
k221 Hev b 8, Lattice, Profilina (Hevea brasiliensis) Allergeni molecolari 009068A.70 IGE SPEC.RICOMB.MOL. - rHev b 8
k224 Hev b 11, Lattice (Hevea brasiliensis) Allergeni molecolari 009068A.66 IGE SPEC.RICOMB.MOL. - rHev b 11
k87 Asp o 21, Alpha-amilasi (Aspergillus oryzae) Allergeni molecolari 009068A.05 IGE SPEC.RICOMB.MOL. - nAsp o 21
m218 Asp f 1 (Aspergillus fumigatus) Allergeni molecolari 009068A.36 IGE SPEC.RICOMB.MOL. - rAsp f 1
m219 Asp f 2 (Aspergillus fumigatus) Allergeni molecolari 009068A.37 IGE SPEC.RICOMB.MOL. - rAsp f 2
m221 Asp f 4 (Aspergillus fumigatus) Allergeni molecolari 009068A.39 IGE SPEC.RICOMB.MOL. - rAsp f 4
m222 Asp f 6 (Aspergillus fumigatus) Allergeni molecolari 009068A.40 IGE SPEC.RICOMB.MOL. - rAsp f 6
m229 Alt a 1 (Alternaria alternata) Allergeni molecolari 009068A.23 IGE SPEC.RICOMB.MOL. - rAlt a 1
o214 MUXF3 CCD, Bromelina Allergeni molecolari 009068A.01 IGE SPEC.RICOMB.MOL. - MUXF3 CCD
o215 Galactose-alpha-1,3-Galactose (alpha-Gal) Tireoglobulina, bovina Allergeni molecolari 009068A.97 IGE SPEC.RICOMB.MOL. -nGal-alpha-1,3-Gal (alpha-Gal)
t215 Bet v1, Betulla, PR-10 (Betula verrucosa) Allergeni molecolari 009068A.42 IGE SPEC.RICOMB.MOL. - rBet v 1
t216 Bet v2, Betulla, Profilina (Betula verrucosa) Allergeni molecolari 009068A.43 IGE SPEC.RICOMB.MOL. - rBet v 2
t224 Ole e 1, Olivo (Olea europaea) Allergeni molecolari 009068A.75 IGE SPEC.RICOMB.MOL. - rOle e 1
t226 Cup a 1, Cipresso (Cupressus arizonica) Allergeni molecolari 009068A.11 IGE SPEC.RICOMB.MOL. - nCup a 1
t227 Ole e 7 Olivo (Olea europaea) Allergeni molecolari 009068A.20 IGE SPEC.RICOMB.MOL. - nOle e 7
t240 Ole e 9 Olivo (Olea europaea) Allergeni molecolari 009068A.76 IGE SPEC.RICOMB.MOL. - rOle e 9
w211 Par j 2, Erba vetriola, LTP (Parietaria judaica) Allergeni molecolari 009068A.77 IGE SPEC.RICOMB.MOL. - rPar j 2
w230 Amb a 1, Ambrosia (Ambrosia elatior) Allergeni molecolari 009068A.02 IGE SPEC.RICOMB.MOL. - nAmb a 1
w231 Art v 1, Assenzio selvatico (Artemisia vulgaris) Allergeni molecolari 009068A.03 IGE SPEC.RICOMB.MOL. - nArt v 1
w233 Art v 3, Assenzio selvatico, LTP (Artemisia vulgaris) Allergeni molecolari 009068A.04 IGE SPEC.RICOMB.MOL. - nArt v 3
c1 Penicilloyl G Farmaci 0090681.T8 IGE SPEC.ALLERG.QUANT. (<5) - c1 - Penicilloyl G
c2 Penicilloyl V Farmaci 0090681.T9 IGE SPEC.ALLERG.QUANT. (<5) - c2 - Penicilloyl V
c202 Succinilcolina (Suxamethonium succinylcholine) Farmaci 0090681.U4 IGE SPEC.ALLERG.QUANT. (<5) - c202 - Succinilcolina
c260 Morfina (Morphine) Farmaci 0090681.U5 IGE SPEC.ALLERG.QUANT. (<5) - c260 - Morfina
c5 Ampicillina (Ampicilloyl) Farmaci 0090681.U0 IGE SPEC.ALLERG.QUANT. (<5) - c5 -Ampicillina
c6 Amoxicillina (Amoxicilloyl) Farmaci 0090681.U1 IGE SPEC.ALLERG.QUANT. (<5) - c6 -Amoxicillina
c7 Cefaclor Farmaci 0090681.U2 IGE SPEC.ALLERG.QUANT. (<5) - c7 -Cefaclor
c73 Insulina umana (Insulin human) Farmaci 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
c74 Gelatina (Gelatin bovine) Farmaci 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
c8 Clorexidina (Chlorhexidine) Farmaci 0090681.U3 IGE SPEC.ALLERG.QUANT. (<5) - c8 - Clorexidina
d1 Dermatophagoides pteronyssinus Inalanti 0090681.B4 IGE SPEC.ALLERG.QUANT. (<5) - d1 - Dermatophagoides pteronyssinus
d2 Dermatophagoides farinae Inalanti 0090681.B5 IGE SPEC.ALLERG.QUANT. (<5) - d2 - Dermatophagoides farinae
d201 Blomia tropicalis Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
d3 Dermatophagoides microceras Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
d70 Acarus siro Inalanti 0090681.B6 IGE SPEC.ALLERG.QUANT. (<5) - d70 - Acarus siro
d71 Lepidoglyphus destructor Inalanti 0090681.B7 IGE SPEC.ALLERG.QUANT. (<5) - d71 - Lepidoglyphus destructor
d72 Tyrophagus putrescentiae Inalanti 0090681.B8 IGE SPEC.ALLERG.QUANT. (<5) - d72 - Tyrophagus putrescentiae
d73 Glycophagus domesticus Inalanti 0090681.B9 IGE SPEC.ALLERG.QUANT. (<5) - d73 - Glycophagus domesticus
d74 Euroglyphus maynei Inalanti 0090681.C0 IGE SPEC.ALLERG.QUANT. (<5) - d74 - Euroglyphus maynei
e1 Epitelio di gatto Inalanti 0090681.C1 IGE SPEC.ALLERG.QUANT. (<5) - Forfora di gatto
e3 Forfora di cavallo Inalanti 0090681.C2 IGE SPEC.ALLERG.QUANT. (<5) - Forfora di cavallo
e4 Forfora di vacca Inalanti 0090681.C3 IGE SPEC.ALLERG.QUANT. (<5) - Forfora di vacca
e5 Forfora di cane Inalanti 0090681.C4 IGE SPEC.ALLERG.QUANT. (<5) - Forfora di cane
e70 Piume d'oca Inalanti 0090681.C6 IGE SPEC.ALLERG.QUANT. (<5) - Piuma d'oca
e71 Epitelio di topo Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
e80 Epitelio di capra Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
e82 Epitelio di coniglio Inalanti 0090681.C8 IGE SPEC.ALLERG.QUANT. (<5) - Epitelio di coniglio
e83 Epitelio di maiale Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
e84 Epitelio di criceto Inalanti 0090681.C9 IGE SPEC.ALLERG.QUANT. (<5) - Epitelio di criceto
e85 Piume di pollo Inalanti 0090681.D1 IGE SPEC.ALLERG.QUANT. (<5) - Piume di pollo
g2 Erba canina (Cynodon dactylon) Inalanti 0090681.A1 IGE SPEC.ALLERG.QUANT. (<5) - g2 - Erba canina
g6 Coda di topo (Phleum pratense) Inalanti 0090681.A5 IGE SPEC.ALLERG.QUANT. (<5) - g6 - Coda di topo
k75 ISOCIANATO TDI Inalanti 0090681.T1 IGE SPEC.ALLERG.QUANT. (<5) - k75 - Isocianato TDI
k76 ISOCIANATO MDI Inalanti 0090681.T2 IGE SPEC.ALLERG.QUANT. (<5) - k76 - Isocianato MDI
k77 ISOCIANATO HDI Inalanti 0090681.T3 IGE SPEC.ALLERG.QUANT. (<5) - k77 - Isocianato HDI
k78 Ossido di etilene Inalanti 0090681.T4 IGE SPEC.ALLERG.QUANT. (<5) - k78 - Ossido di etilene
k79 Anidride ftalica Inalanti 0090681.T5 IGE SPEC.ALLERG.QUANT. (<5) - k79 - Anidride ftalica
k80 Formalina/Formaldeide Inalanti 0090681.T6 IGE SPEC.ALLERG.QUANT. (<5) - k80 - Formaldeide/Formalina
k82 Lattice Inalanti 0090681.T7 IGE SPEC.ALLERG.QUANT. (<5) - k82 - Lattice
m1 Penicillium notatum Inalanti 0090681.D2 IGE SPEC.ALLERG.QUANT. (<5) - m1 - Penicil. chrysogenum (P. notatum)
m2 Cladosporium Herbarum Inalanti 0090681.D3 IGE SPEC.ALLERG.QUANT. (<5) - m2 - Cladosporium herbarum
m207 Aspergillus niger Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
m3 Aspergillus fumigatus Inalanti 0090681.D4 IGE SPEC.ALLERG.QUANT. (<5) - m3 - Aspergillus fumigatus
m4 Mucor Racemosus Inalanti 0090681.D5 IGE SPEC.ALLERG.QUANT. (<5) - m4 - Mucor racemosus
m5 Candida Albicans Inalanti 0090681.D6 IGE SPEC.ALLERG.QUANT. (<5) - m5 - Candida Albicans
m6 Alternaria alternata Inalanti 0090681.D7 IGE SPEC.ALLERG.QUANT. (<5) - m6 - Alternaria alternata
Rm209 Penicillum glabrum Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rt213 Pino (Pinus radiata) Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
t1 Acero (Acer negundo) Inalanti 0090681.E2 IGE SPEC.ALLERG.QUANT. (<5) - t1 - Acero
t11 Platano (Platanus acerifolia) Inalanti 0090681.F1 IGE SPEC.ALLERG.QUANT. (<5) - t11 - Platano
t14 Pioppo (Populus deltoides) Inalanti 0090681.F3 IGE SPEC.ALLERG.QUANT. (<5) - t14 - Pioppo
t203 Ippocastano (Aesculus hippocastanum) Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
Rt206 Castagno (Castanea sativa) Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
t208 Tiglio (Tilia cordata) Inalanti 0090681.F8 IGE SPEC.ALLERG.QUANT. (<5) - t208 - Tiglio
t212 Cedro (Libocedrus decurrens) Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
t23 Cipresso mediterraneo (Cupressus sempervirens) Inalanti 0090681.F7 IGE SPEC.ALLERG.QUANT. (<5) - t23 - Cipresso mediterraneo
t3 Betulla (Betula verrucosa) Inalanti 0090681.E4 IGE SPEC.ALLERG.QUANT. (<5) - t3 - Betulla
t4 Nocciolo (Corylus avellana) Inalanti 0090681.E5 IGE SPEC.ALLERG.QUANT. (<5) - t4 - Nocciolo
t5 Faggio americano (Fagus grandifolia) Inalanti 0090681.E6 IGE SPEC.ALLERG.QUANT. (<5) - t5 - Faggio americano
t8 Olmo americano (Ulmus americana) Inalanti 0090681.E9 IGE SPEC.ALLERG.QUANT. (<5) - t8 - Olmo americano
t9 Olivo (Olea europaea) Inalanti 0090681.F0 IGE SPEC.ALLERG.QUANT. (<5) - t9 - Olivo
w1 Ambrosia comune artemisiifolia (Ambrosia elator) Inalanti 0090681.F9 IGE SPEC.ALLERG.QUANT. (<5) - w01 - Ambrosia comune
w10 Farinaccio selvatico (Chenopodium album) Inalanti 0090681.G7 IGE SPEC.ALLERG.QUANT. (<5) - w10 - Farinaccio selvatico
w12 Verga d'oro (Solidago virgaurea) Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
w204 Girasole (Helianthus annuus) Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
w21 Parietaria judaica Inalanti 0090681.G9 IGE SPEC.ALLERG.QUANT. (<5) - w21 - Parietaria judaica
w45 Erba medica (Medicago sativa) Inalanti 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
w6 Assenzio selvatico (Artemisia vulgaris) Inalanti 0090681.G3 IGE SPEC.ALLERG.QUANT. (<5) - w06 - Assenzio selvatico
w8 Dente di leone (Taraxacum volgare) Inalanti 0090681.G5 IGE SPEC.ALLERG.QUANT. (<5) - w08 - Tarassaco comune
w9 Lanciuola (Plantago lanceolata) Inalanti 0090681.G6 IGE SPEC.ALLERG.QUANT. (<5) - w09 - Lanciuola
i1 Ape (Apis mellifera) Veleni 0090681.S0 IGE SPEC.ALLERG.QUANT. (<5) - i1 - Ape
i2 Calabrone bianco (Dolichovespula maculata) Veleni 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
i204 Tafano (Tabanus spp.) Veleni 0090681.S9 IGE SPEC.ALLERG.QUANT. (<5) - i204 - Tafano
i205 Bombo (Bombus terrestris) Veleni 0090681.T0 IGE SPEC.ALLERG.QUANT. (<5) - i205 - Bombo
i3 Giallone (Vespula spp.) Veleni 0090681.S1 IGE SPEC.ALLERG.QUANT. (<5) - i3 - Vespula spp (giallone)
i4 Vespa (Polistes spp.) Veleni 0090681.00 IGE SPEC. ALLERGOLOGICHE QUANT. SINGOLO ALLERGENE (<5)
i5 Calabrone giallo (Dolichovespula arenaria) Veleni 0090681.S2 IGE SPEC.ALLERG.QUANT. (<5) - i5 - Dolichovesp. aren. (calabr. giallo)
i6 Scarafaggio (Blatella germanica) Veleni 0090681.S3 IGE SPEC.ALLERG.QUANT. (<5) - i6 - Scarafaggio (Blatella germanica)
i70 Formica (Solenopsis invicta) Veleni 0090681.S4 IGE SPEC.ALLERG.QUANT. (<5) - i70 - Formica (Solenopsis invicta)
i71 Zanzara comune (Aedes communis) Veleni 0090681.S5 IGE SPEC.ALLERG.QUANT. (<5) - i71 - Zanzara comune
i75 Calabrone europeo (Vespa crabro) Veleni 0090681.S7 IGE SPEC.ALLERG.QUANT. (<5) - i75 - Vespa crabro (calabrone europeo)
i77 Vespa europea (Polistes dominulus) Veleni 0090681.S8 IGE SPEC.ALLERG.QUANT. (<5) - i77 - Polistes dominulus (vespa europea)"""

TYPES = ["Allergeni molecolari", "Alimenti", "Inalanti", "Farmaci", "Veleni"]


def parse():
    seen = set()
    out = []
    for line in RAW.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        code, _, rest_all = line.partition(" ")
        chosen = None
        for t in TYPES:
            marker = " " + t + " "
            idx = rest_all.find(marker)
            if idx != -1:
                after = rest_all[idx + len(marker):].strip()
                if after.startswith("009068"):
                    chosen = (t, idx, after)
                    break
        if not chosen:
            raise ValueError(f"Impossibile analizzare la riga: {line}")
        t, idx, after = chosen
        name = rest_all[:idx].strip()
        siss_code, _, siss_desc = after.partition(" ")
        if code in seen:
            continue
        seen.add(code)
        out.append({
            "code": code,
            "name": name,
            "type": t,
            "siss_code": siss_code.strip(),
            "siss_description": siss_desc.strip(),
        })
    return out


if __name__ == "__main__":
    data = parse()
    Path(__file__).parent.joinpath("allergens.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    from collections import Counter
    print(f"Totale allergeni: {len(data)}")
    print(Counter(d["type"] for d in data))
