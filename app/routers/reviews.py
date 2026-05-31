from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.db_depends import get_async_db
from app.shemas import ReviewCreate, Review as ReviewSchema
from app.models.reviews import Review as ReviewModel
from app.models.products import Product as ProductModel
from app.models.users import User as UserModel
from app.auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


async def update_product_rating(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    query = await db.scalars(select(ProductModel).where(ProductModel.id == product_id,
                                                        ProductModel.is_active == True))
    product = query.first()
    if product:
        product.rating = avg_rating
        await db.commit()


@router.get("/reviews", response_model=list[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    all_reviews = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    return all_reviews.all()


@router.get("/products/{product_id}/reviews", response_model=list[ReviewSchema])
async def get_review_by_id(product_id: int, db: AsyncSession = Depends(get_async_db)):
    product = await db.scalars(select(ProductModel).where(ProductModel.id == product_id,
                                                          ProductModel.is_active == True))
    result = product.first()
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")

    review = await db.scalars(select(ReviewModel).where(ReviewModel.product_id == product_id,
                                                        ReviewModel.is_active == True))
    db_reviews = review.all()
    return db_reviews


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(review: ReviewCreate, db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "buyer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only buyers can leave reviews")

    product = await db.scalars(select(ProductModel).where(ProductModel.id == review.product_id,
                                                          ProductModel.is_active == True))
    if not product.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    db_review = ReviewModel(**review.model_dump(), user_id = current_user.id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    await update_product_rating(db = db, product_id=review.product_id)
    return db_review



@router.delete("/{review_id}", response_model= ReviewSchema)
async def del_review(
    review_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    result = await db.scalars(select(ReviewModel).where(ReviewModel.id == review_id,
                                                        ReviewModel.is_active == True))
    review = result.first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You do not have permission to delete this review")


    await db.execute(
        update(ReviewModel).where(ReviewModel.id == review_id).values(is_active = False)
    )
    await  db.commit()
    await db.refresh(review)
    await update_product_rating(db, review.product_id)
    return review