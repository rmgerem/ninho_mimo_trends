import logging
from sqlalchemy import create_engine, text
from ninho_mimo_trends.configuration.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_indications():
    settings = Settings()
    engine = create_engine(settings.database_url)
    
    with engine.begin() as conn:
        # First, find scores >= 40 that are not in tb_product_indications
        result = conn.execute(text("""
            SELECT ps.id, ps.product_id, ps.opportunity_score, ps.risk_score, ps.trend_status, ps.calculated_at, p.category_id
            FROM tb_product_scores ps
            JOIN tb_products p ON p.id = ps.product_id
            WHERE ps.opportunity_score >= 40
            AND ps.id NOT IN (SELECT product_score_id FROM tb_product_indications)
        """))
        
        rows = result.fetchall()
        if not rows:
            logger.info("Nenhum produto precisava ser corrigido. (Nenhum score >= 40 faltando).")
            return
            
        logger.info(f"Encontrados {len(rows)} produtos com nota >= 40 que precisam ser inseridos no painel.")
        
        for row in rows:
            conn.execute(text("""
                INSERT INTO tb_product_indications (product_id, product_score_id, category_id, opportunity_score, risk_score, trend_status, indicated_at)
                VALUES (:product_id, :product_score_id, :category_id, :opportunity_score, :risk_score, :trend_status, :indicated_at)
                ON CONFLICT (product_score_id) DO NOTHING
            """), {
                "product_id": row.product_id,
                "product_score_id": row.id,
                "category_id": row.category_id,
                "opportunity_score": row.opportunity_score,
                "risk_score": row.risk_score,
                "trend_status": row.trend_status,
                "indicated_at": row.calculated_at
            })
            
        logger.info(f"Sucesso! {len(rows)} produtos foram forcados para o painel de indicacoes!")

if __name__ == "__main__":
    fix_indications()
