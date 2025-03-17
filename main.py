import os
import asyncio
import streamlit as st
from dotenv import load_dotenv
from functions.product_details import product_categories, product_images
from functions.pdf import parse_recipe_name, create_pdf
from functions.recipeProcessor import (
    get_pdf_texts,
    create_knowledge_hub,
    generate_recipe,
    stream_data,
    generate_recipe_image,
)
from services.constants import CANPREV_IMAGE_PATH

load_dotenv(override=True)


async def main():
    st.set_page_config(page_title="Recipe Generator", page_icon="🍲", layout="wide")

    # Main Title & Intro
    st.title("Recipe Generator")
    st.info(
        """
        Welcome to Canprev's Recipe Generator!
        Select one or more categories, then choose products from those categories,
        optionally provide custom instructions, and click **Generate Recipe**.
        """
    )

    # -------------------------
    # SIDEBAR: Category and Product Selection
    # -------------------------
    with st.sidebar:
        st.image(CANPREV_IMAGE_PATH, width=160)
        st.header("Select Categories")
        selected_categories = st.multiselect(
            "Product Categories:", options=list(product_categories.keys())
        )

        # Build a combined product list from the chosen categories
        available_products = []
        if selected_categories:
            for cat in selected_categories:
                available_products.extend(product_categories.get(cat, []))
            available_products = sorted(list(set(available_products)))
        else:
            available_products = []

        st.header("Select Products")
        selected_products = st.multiselect("Products:", options=available_products)

        # Show images of selected products (if any)
        if selected_products:
            st.markdown("#### Selected Products")
            for prod in selected_products:
                img_path = product_images.get(prod)
                if img_path and os.path.exists(img_path):
                    st.image(img_path, caption=prod, use_container_width=True)
                else:
                    st.warning(f"Image not found for {prod}")

        # Option to build/update the knowledge base
        if st.button("Build/Update Knowledge Base", type="primary"):
            with st.spinner("Building the knowledge base from PDF files..."):
                documents = get_pdf_texts()
                create_knowledge_hub(documents)
                st.success("Knowledge Base updated successfully!")

    # Optional custom instructions
    custom_instructions = ""
    with st.expander("Custom Recipe Instructions (Optional)"):
        custom_instructions = st.text_area(
            label="Describe how you want the recipe to be...",
            placeholder="e.g. healthy, vegan, spicy, low-calorie, extra protein...",
            height=68,
        )

    # Generate Recipe Button
    if st.button("Generate Recipe", type="primary"):
        if not selected_products:
            st.warning("Please select at least one product.")
        else:
            with st.spinner(
                "Hold on... our genius chef is busy inventing a recipe for you...!"
            ):
                # Combine selected products into a single query
                final_query = " ".join(selected_products)
                # Append any custom instructions
                if custom_instructions.strip():
                    final_query = f"generate a recipe using {final_query} and I want {custom_instructions.strip()}"
                    # final_query += " " + custom_instructions.strip()

                # 1) Generate the recipe text
                recipe_text = await generate_recipe(final_query)
                # 2) Extract recipe name (if any)
                recipe_name, cleaned_text = parse_recipe_name(recipe_text["output"])
                # 3) Generate the recipe image
                recipe_image_url = await generate_recipe_image(recipe_text["output"])

            # Display results in a two-column layout
            col1, col2 = st.columns([2, 1])
            with col2:
                st.markdown("### Recipe Image")
                if recipe_image_url:
                    st.image(
                        recipe_image_url,
                        caption=", ".join(selected_products),
                        width=400,
                    )
                else:
                    st.warning("Could not generate recipe image.")

            with col1:
                st.markdown("### Recipe Details")
                with st.spinner("Chef's recipe is almost ready..."):
                    await asyncio.sleep(2)
                st.write_stream(stream_data(recipe_text["output"]))

                # Offer a PDF download
                if recipe_image_url and cleaned_text:
                    pdf_bytes = create_pdf(recipe_name, recipe_image_url, cleaned_text)
                    if pdf_bytes:
                        safe_name = recipe_name if recipe_name else "Recipe"
                        st.download_button(
                            label="Download Recipe as PDF",
                            data=pdf_bytes,
                            file_name=f"{safe_name}_recipe.pdf",
                            mime="application/pdf",
                            type="primary",
                        )
                    else:
                        st.error("Error generating PDF.")


if __name__ == "__main__":
    asyncio.run(main())
