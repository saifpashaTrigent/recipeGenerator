import os
import asyncio
import streamlit as st
from dotenv import load_dotenv
from functions.product_details import product_categories, product_images
from functions.pdf import parse_recipe_name, create_pdf
from functions.doc_processor import (
    get_pdf_texts,
    create_knowledge_hub,
    generate_recipe,  
    stream_data,
    generate_recipe_image
)
from services.constants import CANPREV_IMAGE_PATH

load_dotenv(override=True)


async def main():
    st.set_page_config(page_title="Recipe Generator", page_icon="🍲", layout="wide")

    st.title("Recipe Generator")
    st.info(
        """
        Welcome to Canprev's Recipe Generator! 
        Select your Product and click **Generate Recipe**.
        """
    )

    with st.sidebar:
        st.image(CANPREV_IMAGE_PATH, width=160)
        st.header("Select Products")
        selected_category = st.selectbox(
            "Product Category:", list(product_categories.keys())
        )
        selected_product = st.selectbox(
            "Product Name:", product_categories[selected_category]
        )

        # Display product image in sidebar if available.
        image_path_sidebar = product_images.get(selected_product)
        if image_path_sidebar and os.path.exists(image_path_sidebar):
            st.image(image_path_sidebar, use_container_width=True)
        else:
            st.warning(f"Image not found: {image_path_sidebar}")

        if st.button("Build/Update Knowledge Base", type="primary"):
            with st.spinner("Building the knowledge base from PDF files..."):
                documents = get_pdf_texts()
                create_knowledge_hub(documents)
                st.success("Knowledge Base updated successfully!")


    custom_instructions = ""
    with st.expander("Custom Recipe Instructions (Optional)"):
        custom_instructions = st.text_area(
            label="Describe how you want the recipe to be...",
            placeholder="e.g. healthy, vegan, spicy, low-calorie, extra protein...",
            height=68,
        )

    if st.button("Generate Recipe", type="primary"):
        with st.spinner(
            "Hold on... our genius chef is busy inventing a recipe for you...!"
        ):
            final_query = selected_product
            if custom_instructions.strip():
                final_query += " " + custom_instructions.strip()

            # 1) Generate recipe text.
            recipe_text = await generate_recipe(final_query)

            # 2) Extract recipe name (if present) from the text.
            recipe_name, cleaned_text = parse_recipe_name(recipe_text["output"])

            # 3) Generate the recipe image.
            recipe_image_url = await generate_recipe_image(recipe_text["output"])

        col1, col2 = st.columns([2, 1])
        with col2:
            st.markdown("### Recipe Image")
            if recipe_image_url:
                st.image(recipe_image_url, caption=selected_product, width=400)
            else:
                st.warning("Could not generate recipe image.")

        with col1:
            st.markdown("### Recipe Details")
            with st.spinner("Chef's recipe is almost ready..."):
                await asyncio.sleep(3)
            st.write_stream(stream_data(recipe_text["output"]))

            # Generate PDF and allow download.
            if recipe_image_url and cleaned_text:
                pdf_bytes = create_pdf(recipe_name, recipe_image_url, cleaned_text)
                if pdf_bytes:
                    # If there's no recognized recipe name, we fallback to something like "Recipe"
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
