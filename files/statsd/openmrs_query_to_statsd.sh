# number of HIV positive patients
echo "openmrs.HIV_postitive_patient.count:`echo \
"SELECT count(distinct person_id) FROM openmrs.obs WHERE \
concept_id=160554;" | \
mysql --database=openmrs --skip-column-names`|c" | nc -w 1 -u 127.0.0.1 8125

# number of CD4 cell count in past 6 months 
echo "openmrs.6mo_CD4_cell_count.count:`echo \
"SELECT count(DISTINCT PERSON_ID) FROM openmrs.obs where concept_id = 730 \
AND PERIOD_DIFF(EXTRACT(YEAR_MONTH FROM NOW()), EXTRACT(YEAR_MONTH \
FROM OBS_DATETIME)) <= 6;" | \
mysql --database=openmrs --skip-column-names`|c" | nc -w 1 -u 127.0.0.1 8125
