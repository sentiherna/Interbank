CREATE TABLE "disc_comercial"."plaft_pj_minorista_0426" WITH (
     format = 'parquet',
  external_location = 's3://ibk-discovery-comercial-us-east-1-654654352211-data/discovery/comercial/sanherna/PLAFT/PJ/MINORISTA/DATA_INFERENCIA_PILOTO/INFERENCIA/',
  partitioned_by = ARRAY [ 'periodo' ]
) AS

WITH pd AS (
    SELECT DISTINCT
        -- Identificadores
        a.key_value,
        a.cod_cli,
        date_format(
            date_parse(CAST(a.cod_mes AS varchar), '%Y%m') - interval '1' month,
            '%Y%m'
        ) AS codmes_lag1,
        CAST(a.cod_mes AS INTEGER) AS cod_mes,

        -- Fechas
        TRY_CAST(a.fec_constitucion AS DATE) AS fec_constitucion,

        -- Monetarios
        TRY_CAST(a.mto_pas_soles AS DOUBLE) AS mto_pas_soles,
        TRY_CAST(a.imp_trx_abonosefect_6m AS DOUBLE) AS imp_trx_abonosefect_6m,
        TRY_CAST(a.imp_trx_cargosefe_6m AS DOUBLE) AS imp_trx_cargosefe_6m,
        TRY_CAST(a.avg_trx_cargostot_3m AS DOUBLE) AS avg_trx_cargostot_3m,
    TRY_CAST(a.max_trx_abonos_3m AS DOUBLE) AS max_trx_abonos_3m,

        -- Cantidades
        TRY_CAST(a.cnt_trx_cargostot_3m AS INTEGER) AS cnt_trx_cargostot_3m,

        -- Promedios / ratios
        TRY_CAST(a.cnt_trx_abonospromtot_3m AS DOUBLE) AS cnt_trx_abonospromtot_3m,
        TRY_CAST(a.rat_trx_abonosefectot_1m AS DOUBLE) AS rat_trx_abonosefectot_1m,
        TRY_CAST(a.rat_trx_abonosefectot_3m AS DOUBLE) AS rat_trx_abonosefectot_3m,
        TRY_CAST(a.rat_trx_abonosefectot_9m AS DOUBLE) AS rat_trx_abonosefectot_9m,
        TRY_CAST(a.rat_mntcrgsefetot_1m AS DOUBLE) AS rat_mntcrgsefetot_1m,

        -- Demográficas / antigüedad
        TRY_CAST(a.num_edad_constitucion AS INTEGER) AS num_edad_constitucion,
    TRY_CAST(a.num_antiguedad AS INTEGER) AS num_antiguedad,

        -- Riesgo
        TRY_CAST(a.desc_nivel_rsg_lsb_tot AS DOUBLE) AS desc_nivel_rsg_lsb_tot,

        -- Actividad mensual
        TRY_CAST(a.cnt_meses_siningresos_12m AS INTEGER) AS cnt_meses_siningresos_12m,
        TRY_CAST(a.cnt_meses_sinegresos_12m AS INTEGER) AS cnt_meses_sinegresos_12m,

        -- Ubicación / segmentación
        a.desc_provincia,
        a.desc_departamento,
        a.cod_ubigeo_cd,
        a.cod_sectorista_id,
        a.cod_ciiu_v4,

        -- Flags (string/bool → 0/1)
        CAST(a.flg_casos_hist AS INTEGER) AS flg_casos_hist,
        CAST(a.flg_vrcn_abonos_5m_1m AS INTEGER) AS flg_vrcn_abonos_5m_1m,
        CAST(a.flg_vrcn_efe_cargos_5m_1m AS INTEGER) AS flg_vrcn_efe_cargos_5m_1m,

        -- Conteos
        a.cnt_ro_debajo_umbral,
        -- Perfil económico
        a.mto_fact_declarado_sunat,
        TRY_CAST(a.avg_cp_men_ing_12m AS DOUBLE) AS avg_cp_men_ing_12m,
        TRY_CAST(a.avg_cpmenegr_12m AS DOUBLE) AS avg_cpmenegr_12m,
        TRY_CAST(a.max_mto_cpmening_12m AS DOUBLE) AS max_mto_cpmening_12m,
        TRY_CAST(a.max_mto_cpegrmen_12m AS DOUBLE) AS max_mto_cpegrmen_12m,

        -- Exterior
        a.flg_al_ext_12m,
        a.flg_del_ext_12m,
        TRY_CAST(a.cnt_trx_sinenv_alext_12m AS INTEGER) AS cnt_trx_sinenv_alext_12m,
        TRY_CAST(a.cnt_trx_al_ext_1000_12m AS INTEGER) AS cnt_trx_al_ext_1000_12m,
        TRY_CAST(a.mto_al_ext_12m AS DOUBLE) AS mto_al_ext_12m,
        TRY_CAST(a.mto_del_ext_12m AS DOUBLE) AS mto_del_ext_12m,

        -- Reputacional / antecedentes
        a.flg_pep,
        a.cod_rsg_pep,
        a.flg_activo_pep,
        TRY_CAST(a.cnt_noticias AS INTEGER) AS cnt_noticias,
        a.flg_ros_12m,
        a.flg_alerta_12m,
        TRY_CAST(a.cnt_alerta_hist AS INTEGER) AS cnt_alerta_hist,
        TRY_CAST(a.cnt_ros_hist AS INTEGER) AS cnt_ros_hist,

        -- KYC
        a.flg_kyc_12m,
        a.flg_kyc_hist,
        TRY_CAST(a.cnt_kyc_hist AS INTEGER) AS cnt_kyc_hist,
        -- ======================================================
        -- 🔹 ACELERACIÓN / CAMBIO DE COMPORTAMIENTO
        -- ======================================================
        TRY_CAST(a.imp_trx_abonostot_1m AS DOUBLE)
            / NULLIF(TRY_CAST(a.avg_trx_abonostot_6m AS DOUBLE), 0)
            AS ratio_abonos_1m_vs_6m,

        TRY_CAST(a.imp_trx_cargostot_1m AS DOUBLE)
            / NULLIF(TRY_CAST(a.avg_trx_cargostot_6m AS DOUBLE), 0)
            AS ratio_cargos_1m_vs_6m,


        -- ======================================================
        -- 🔹 CONCENTRACIÓN EN CONTRAPARTE
        -- ======================================================
        TRY_CAST(a.avg_cpmenegr_12m AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_cargostot_6m AS DOUBLE), 0)
            AS share_cp_egresos,

        TRY_CAST(a.avg_cp_men_ing_12m AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_abonostot_6m AS DOUBLE), 0)
            AS share_cp_ingresos,


        -- ======================================================
        -- 🔹 NORMALIZACIÓN DE RIESGO
        -- ======================================================
        TRY_CAST(a.cnt_ros_hist AS DOUBLE)
            / NULLIF(TRY_CAST(a.cnt_trx_cargostot_3m AS DOUBLE), 0)
            AS ros_por_trx_3m,

        TRY_CAST(a.cnt_alerta_hist AS DOUBLE)
            / NULLIF(TRY_CAST(a.num_antiguedad AS DOUBLE), 0)
            AS alertas_por_antiguedad,


        -- ======================================================
        -- 🔹 COHERENCIA ECONÓMICA
        -- ======================================================
        TRY_CAST(a.imp_trx_abonostot_6m AS DOUBLE)
            / NULLIF(TRY_CAST(a.mto_fact_declarado_sunat AS DOUBLE), 0)
            AS ingresos_vs_facturacion,

        TRY_CAST(a.mto_pas_soles AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_abonostot_6m AS DOUBLE), 0)
            AS pasivo_vs_ingresos,



        -- ======================================================
        -- 🔹 EXPOSICIÓN AL EXTERIOR (PROPORCIONES)
        -- ======================================================
        TRY_CAST(a.mto_al_ext_12m AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_abonostot_12m AS DOUBLE), 0)
            AS ratio_egresos_exterior,

        TRY_CAST(a.mto_del_ext_12m AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_abonostot_12m AS DOUBLE), 0)
            AS ratio_ingresos_exterior,


        -- ======================================================
        -- 🔹 COHERENCIA PEP / LSB
        -- ======================================================
        TRY_CAST(a.cod_rsg_pep AS DOUBLE)
            - TRY_CAST(a.desc_nivel_rsg_lsb_tot AS DOUBLE)
            AS gap_riesgo_pep_lsb

    FROM e_perm_aws.t_agg_alertas_plaft a
    WHERE a.cod_mes = '202604'
      AND a.desc_subsegmento = 'BPE'
),

target AS (
 SELECT *
FROM (
    SELECT
        codunico,
        CAST(REPLACE(SUBSTRING(CAST(alerta_fecha AS VARCHAR),1,7),'-','') AS VARCHAR) AS periodo_alerta,
        tipo_alerta_n2,
        trx_riesgo_cliente,
        ROW_NUMBER() OVER (
            PARTITION BY codunico,
                         REPLACE(SUBSTRING(CAST(alerta_fecha AS VARCHAR),1,7),'-','')
            ORDER BY CASE
                WHEN tipo_alerta_n2 = 'MANUAL' THEN 1
                WHEN tipo_alerta_n2 = 'SEMI AUTOMATICA' THEN 2
                WHEN tipo_alerta_n2 = 'AUTOMATICO' THEN 3
                ELSE 99
            END
        ) AS rn,
        MAX(CAST (orden_alerta AS INT )) AS flg_alerta
    FROM e_perm_aws.t_alertas_plaft
    GROUP BY
        codunico,
        REPLACE(SUBSTRING(CAST(alerta_fecha AS VARCHAR),1,7),'-',''),
        tipo_alerta_n2,
        trx_riesgo_cliente
) t
WHERE rn = 1)

SELECT 
    a.*,
    b.tipo_alerta_n2,
    b.trx_riesgo_cliente,
    CASE 
        WHEN b.flg_alerta = 1 THEN 1 
        ELSE 0 
    END AS target_m,
    b.periodo_alerta,
    a.cod_mes as periodo
FROM pd a
LEFT JOIN target b
    ON a.cod_cli = b.codunico
    AND cast(a.codmes_lag1 as varchar) = b.periodo_alerta