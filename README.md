TPS BDDA

// J'ai exÃ©cutÃ© toutes les requÃªtes, elles fontionnent toutes.
// Qu'Allah vous accorde de la rÃ©ussite, bon courage :))

## TP02

```sql
CREATE TYPE  adresse_type AS OBJECT (   numRue VARCHAR(35),
                                        nomRue VARCHAR(30),
                                        codePostal VARCHAR(10),
                                        ville VARCHAR(25)
                                        ) NOT FINAL;
```

```sql
CREATE TYPE  adresseWithEmail_type UNDER adresse_type 
( adresseEmail VARCHAR(20));
```

```sql
CREATE TYPE personne_type AS OBJECT (numero NUMBER(10),
                                     nom VARCHAR(20),
                                     prenom VARCHAR(20),
                                     adresse adresse_type,
                                     age NUMBER(3)) NOT FINAL;
```

```sql
CREATE TYPE etudiant_type UNDER personne_type (numCarte NUMBER(10),
                                               anneeInsc NUMBER(4));
```

```sql
CREATE TYPE enseignant_type UNDER personne_type (grade VARCHAR(20));
```

```sql
CREATE TABLE personnes OF personne_type (
    CONSTRAINT pk_constraint PRIMARY KEY (numero),
    CONSTRAINT ck_constraint CHECK (age BETWEEN 17 AND 60),
    CONSTRAINT nn_ville CHECK (adresse.ville IS NOT NULL))
```

```sql
INSERT INTO personnes VALUES(100,'yasmine','kadi',
adresse_type('5','rue benbouali','bejaia','06000'),30);
```

```sql
INSERT INTO personnes VALUES(enseignant_type(101,'zaid','samir',
adresseWithEmail_type('12','rue didouche','SETIF','19000','kzaidi@estin.dz'),
42,'professeur'));
```

```sql
INSERT INTO personnes VALUES(etudiant_type(102,'salmy','islam',
adresseWithEmail_type('10','rue KRIM BELKACEM','ALGER','16000','nselmy@estin.dz'),
19,100,2018));
```

```sql
SELECT * FROM personnes;

SELECT VALUE(p) FROM personnes p ;

SELECT p.numero, p.nom,p.prenom, TREAT( p.adresse AS adresseWithEmail_type)
FROM personnes p;

SELECT p.numero, p.nom, p.prenom, TREAT(VALUE(p) AS enseignant_type).grade
FROM Personnes p
WHERE VALUE(p) IS OF (enseignant_type);

SELECT p.numero, p.nom, p.prenom, TREAT(VALUE(p) AS etudiant_type).numCarte
FROM Personnes p
WHERE VALUE(p) IS OF (etudiant_type);

SELECT *
FROM personnes p
WHERE value(p) IS OF( ONLY personne_type);

//2eme mÃ©thode:
SELECT *
FROM Personnes P
WHERE VALUE(P) IS NOT OF (etudiant_type)
  AND VALUE(P) IS NOT OF (enseignant_type);
```

## TP03

```sql
CREATE TYPE Ecole AS OBJECT (NomEcole VARCHAR(25));

CREATE TYPE Specialite_type AS OBJECT (NomSpecialite VARCHAR(25), 
                                        ref_ecole REF Ecole);

CREATE TYPE Etudiant_type AS OBJECT ( matricule NUMBER(4), Nom VARCHAR(25),
Prenom VARCHAR(25), ref_specialite REF specialite_type);

CREATE TABLE Ecoles OF Ecole ( CONSTRAINT pk_ecole PRIMARY KEY(NomEcole));

CREATE TABLE specialites OF specialite_type (
            CONSTRAINT pk_spec PRIMARY KEY(NomSpecialite),
            CONSTRAINT nn_ref_ecole CHECK(ref_ecole IS NOT NULL),
            CONSTRAINT ref_ref_ecole ref_ecole REFERENCES Ecoles);
            
CREATE TABLE Etudiants OF etudiant_type (
            CONSTRAINT pk_etud PRIMARY KEY(matricule),
            CONSTRAINT nn_ref_spec CHECK(ref_specialite IS NOT NULL),
            CONSTRAINT ref_ref_spec ref_specialite REFERENCES specialites)
            
```

```sql
INSERT INTO Ecoles VALUES ('ESTIN');
INSERT INTO Ecoles VALUES ('ESI ALG');
INSERT INTO Ecoles VALUES ('ESI SBA');

INSERT INTO specialites VALUES ('IA DS', 
(SELECT REF(e) FROM Ecoles e WHERE e.NomEcole='ESTIN'))

INSERT INTO specialites VALUES ('CS', 
(SELECT REF(e) FROM Ecoles e WHERE e.NomEcole='ESTIN'))

INSERT INTO specialites VALUES ('SIL', 
(SELECT REF(e) FROM Ecoles e WHERE e.NomEcole='ESI ALG'))

INSERT INTO specialites VALUES ('SID', 
(SELECT REF(e) FROM Ecoles e WHERE e.NomEcole='ESI ALG'))

INSERT INTO specialites VALUES ('SIW', 
(SELECT REF(e) FROM Ecoles e WHERE e.NomEcole='ESI SBA'))

INSERT INTO Etudiants VALUES(0111,'Ahmed','Benarab',
(SELECT REF(s) FROM specialites s WHERE s.NomSpecialite='CS'))

INSERT INTO Etudiants VALUES(0112,'Fatima','Khelif',
(SELECT REF(s) FROM specialites s WHERE s.NomSpecialite='SID'))

INSERT INTO Etudiants VALUES(0113,'Youcef','Belhadj',
(SELECT REF(s) FROM specialites s WHERE s.NomSpecialite='IA DS'))

INSERT INTO Etudiants VALUES(0114,'Amina','Kaddour',
(SELECT REF(s) FROM specialites s WHERE s.NomSpecialite='IA DS'))

INSERT INTO Etudiants VALUES(0115,'Karim','Bouzidi',NULL)
// check constraint not null violated 

ALTER TABLE etudiants
DROP CONSTRAINT nn_ref_spec;

INSERT INTO Etudiants VALUES(0115,'Karim','Bouzidi',NULL)
//ligne insÃ©rÃ©e

INSERT INTO Etudiants VALUES(0116,'Nassima','Hamza',
(SELECT REF(s) FROM specialites s WHERE s.NomSpecialite='SID'))

INSERT INTO Etudiants VALUES(0117,'Mohamed','Djelloul',
(SELECT REF(s) FROM specialites s WHERE s.NomSpecialite='CS'))
```

```sql
SELECT REF(e) FROM Ecoles e;
SELECT object_id from Ecoles;
SELECT ROWID from Ecoles;

SELECT DEREF(s.ref_ecole).NomEcole 
FROM specialites s 
WHERE s.NomSpecialite='CS';

SELECT *
FROM specialites s
WHERE s.ref_ecole.NomEcole='ESI ALG';

//2eme mÃ©thode
SELECT *
FROM specialites s
WHERE DEREF(s.ref_ecole).NomEcole='ESI ALG';

SELECT DEREF(DEREF(e.ref_specialite).ref_ecole).NomEcole "Ecole",
COUNT(*) "Nombre d'etudiants"
FROM etudiants e
GROUP BY (DEREF(DEREF(e.ref_specialite).ref_ecole).NomEcole);
```

```sql
UPDATE etudiants
SET ref_specialite=(SELECT REF(s) FROM specialites s WHERE s.NomSpecialite='SIW')
WHERE matricule=0115;
```

## TP02 EXO02

```sql
CREATE TYPE film_type AS OBJECT(nomFilm VARCHAR(25));
CREATE TYPE musique_type AS OBJECT( nomMusic VARCHAR(25));

CREATE TYPE acteur_type AS OBJECT( nomActeur VARCHAR(25),
ref_film REF film_type);
																	 
CREATE TYPE chanteur_type AS OBJECT( nomChanteur VARCHAR(25),*
ref_musique REF musique_type)
```

```sql
CREATE TABLE films OF film_type (CONSTRAINT pk_film PRIMARY KEY(nomFilm));
CREATE TABLE musiques OF musique_type (CONSTRAINT pk_musique PRIMARY KEY(nomMusic));

//j'ai inversÃ© chanteur et acteur (scope is et references)
CREATE TABLE acteurs OF acteur_type (CONSTRAINT pk_acteur PRIMARY KEY(nomActeur),
                                     CONSTRAINT sc_film ref_film SCOPE IS films);
                                     
          
CREATE TABLE chanteurs OF chanteur_type (CONSTRAINT pk_chanteur PRIMARY KEY(nomChanteur),
                                         CONSTRAINT ref_ref_musique ref_musique REFERENCES Musiques);
```

```sql
INSERT INTO musiques VALUES('AYEN AYEN')
INSERT INTO Films VALUES('DA MEZIANE');

INSERT INTO Chanteurs VALUES('MATOUB',
(SELECT REF(m)FROM Musiques m WHERE m.nomMusic='AYEN AYEN'));

INSERT INTO Acteurs VALUES('MEZIANE',
(SELECT REF(f)FROM films f WHERE f.nomfilm='DA MEZIANE'));
```

```sql
DELETE FROM Films
WHERE nomFilm='DA MEZIANE';
//ligne supprimÃ©e

DELETE FROM Musiques
WHERE nomMusic='AYEN AYEN';
//integrity constraint violated - child record found

// REF: A reference data type that points to a specific row in a table.
// SCOPE IS: Limits the reference to a specific table, ensuring
//            referential integrity within that scope.
```

## TP04

```sql
CREATE TYPE Marque AS OBJECT( nom VARCHAR(10),Fournisseur VARCHAR(10));
CREATE TYPE Voile AS OBJECT( numero NUMBER(6),surface NUMBER(3),MarqueV Marque);
CREATE TYPE LesVoiles AS TABLE OF Voile;
CREATE TYPE Moteur AS OBJECT( numero NUMBER(6),Puissance NUMBER(3),MarqueM REF Marque);
CREATE TYPE Bateau AS OBJECT( numero NUMBER(6),MoteurB Moteur, Voiles LesVoiles, 
			      MarqueB REF Marque);
																
CREATE TABLE EnsMarque OF Marque(
CONSTRAINT pk_ensmarque PRIMARY KEY (nom));

CREATE TABLE EnsBateau OF Bateau (
CONSTRAINT pk_ensbateau PRIMARY KEY(numero),
CONSTRAINT un_moteur UNIQUE(MoteurB.numero),
CONSTRAINT nn_marqueb CHECK (marqueB IS NOT NULL),
CONSTRAINT ref_marqueB marqueB REFERENCES Ensmarque )
NESTED TABLE Voiles STORE AS voile_tab
(( CONSTRAINT pk_voiles PRIMARY KEY (numero) ));
```

```sql
INSERT INTO EnsMarque VALUES ('Bobato','Omonbato');

INSERT INTO EnsBateau VALUES (115643,NULL,
LesVoiles(Voile(333412,20,(SELECT REF(e) FROM Ensmarque e WHERE e.nom='Jolivoile'))),
(SELECT REF(s) FROM EnsMarque s WHERE s.nom = 'Bobato') );

UPDATE EnsBateau
SET MoteurB=Moteur(555466,75,(SELECT REF(m) FROM EnsMarque m WHERE nom='Bobato'))
WHERE numero=115643;

```

```sql
SELECT b.numero
FROM EnsBateau b
WHERE  b.MoteurB.Puissance > 50
  AND DEREF(b.MarqueB).fournisseur='Omonbato';

SELECT b.numero
FROM EnsBateau b
WHERE CARDINALITY(b.Voiles) > 4;

SELECT b.MarqueB.nom ,AVG(v.Surface)
FROM EnsBateau b , TABLE( b.Voiles) v
GROUP BY b.MarqueB.nom;
```

## TP05

CREATE TYPE etablissemnt_type AS OBJECT ( code NUMBER(5), nom VARCHAR(25),
																					                          type_etb VARCHAR(25));
																					
CREATE TYPE chercheur_type AS OBJECT ( code NUMBER(5), nom VARCHAR(25),
prenom VARCHAR(25),grade VARCHAR(25),ref_etb REF etablissemnt_type);	

CREATE TYPE chercheur_ref_type AS OBJECT (ref_chercheur REF chercheur_type);

CREATE TYPE chercheur_ref_tab_type AS TABLE OF chercheur_ref_type;

CREATE TYPE projet_type AS OBJECT ( code NUMBER(5), 
                                    intitule VARCHAR(25),
                                    duree VARCHAR(25),
                                    domaine VARCHAR(25),
                                    fiiere VARCHAR(25),
                                    ref_etb_fin REF etablissemnt_type,
                                    membres chercheur_ref_tab_type ,
                                    ref_responsable REF chercheur_type);																		
CREATE TABLE etablissements OF etablissemnt_type(
            CONSTRAINT pk_etb PRIMARY KEY (code));

CREATE TABLE chercheurs OF chercheur_type( 
		      CONSTRAINT pk_ch PRIMARY KEY(code),
                      CONSTRAINT nn_ref_etb CHECK(ref_etb IS NOT NULL),
                      CONSTRAINT ref_ref_etb ref_etb REFERENCES etablissements);
                           
CREATE TABLE projets OF projet_type(
            CONSTRAINT pk_projet PRIMARY KEY(code),
            CONSTRAINT nn_ref_etb_fin CHECK (ref_etb_fin IS NOT NULL),
            CONSTRAINT ref_ref_etb_fin ref_etb_fin REFERENCES etablissements,
            CONSTRAINT nn_ref_responsable CHECK( ref_responsable IS NOT NULL),
            CONSTRAINT ref_ref_responsable ref_responsable REFERENCES chercheurs)
            NESTED TABLE membres STORE AS ch_tab;
                                        
INSERT INTO etablissements VALUES (1,'ESTIN','Ecole Sup');
INSERT INTO etablissements VALUES (2,'ESI ALG','Ecole Sup');

INSERT INTO chercheurs VALUES(1,'AZOUAOU','FAICAL','Pr',
(SELECT REF(e) FROM etablissements e WHERE e.nom='ESTIN'));            

INSERT INTO chercheurs VALUES(2,'KHERBACHI','HAMID','Pr',
(SELECT REF(e) FROM etablissements e WHERE e.nom='ESTIN'));    

INSERT INTO chercheurs VALUES(3,'AHMED NACER','MOHAMED','Pr',
(SELECT REF(e) FROM etablissements e WHERE e.nom='ESTIN'));      

INSERT INTO projets VALUES (2,'SDRF','2022','IGL','GL',
(SELECT REF(e) FROM etablissements e WHERE e.nom='ESTIN'),
chercheur_ref_tab_type(chercheur_ref_type( (SELECT REF(c) FROM chercheurs c WHERE c.nom='AZOUAOU') ),
                       chercheur_ref_type( (SELECT REF(c) FROM chercheurs c WHERE c.nom='AHMED NACER') ) ),
                       (SELECT REF(c) FROM chercheurs c WHERE c.nom='AHMED NACER'));                       

   
SELECT m.ref_chercheur.nom, m.ref_chercheur.prenom
FROM projets p, TABLE(p.membres) m
WHERE p.code=2;                       