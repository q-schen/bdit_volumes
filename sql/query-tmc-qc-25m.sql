﻿SELECT DISTINCT	A.arterycode,
		NULL as num_links,
		B.street1,
		B.street2,
		C.centreline_id,
		D.sideofint,
		D.match_on_case,
		C.feature_code_desc

FROM		(SELECT AR.arterycode, AR.buffloc
		FROM (SELECT arterycode, ST_Buffer(loc,25) as buffloc FROM prj_volume.arteries WHERE tx IS NULL and ty IS NULL AND tnode_id IS NULL ORDER BY arterycode) AR
		INNER JOIN prj_volume.centreline CL ON ST_Intersects(CL.shape, AR.buffloc)
		WHERE CL.feature_code_desc NOT IN ('Geostatistical line', 'Hydro Line','Creek/Tributary','Major Railway','Major Shoreline','Minor Shoreline (Land locked)','Busway','River','Walkway','Ferry Route','Trail')
		GROUP BY AR.arterycode, AR.buffloc
		HAVING COUNT(AR.arterycode) <= 4 AND MIN(CL.shape_length) < 25
		) A
		
INNER JOIN 	traffic.arterydata B USING (arterycode)

INNER JOIN	prj_volume.centreline C ON ST_Intersects(C.shape, A.buffloc)

LEFT JOIN	prj_volume.artery_tcl D USING (centreline_id, arterycode)

WHERE		C.feature_code_desc NOT IN ('Geostatistical line', 'Hydro Line','Creek/Tributary','Major Railway','Major Shoreline','Minor Shoreline (Land locked)','Busway','River','Walkway','Ferry Route','Trail')
		AND B.count_type = 'R' AND D.sideofint IS NULL

ORDER BY	A.arterycode, D.sideofint